import logging
import asyncio
import time
import json
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from .session_manager import SessionManager
from voice.vad import SileroVADWrapper
from voice.speech_to_text import FasterWhisperSTTWrapper
from voice.text_to_speech import KokoroTTSWrapper
import scipy.signal

logger = logging.getLogger(__name__)
ws_router = APIRouter()

session_mgr = SessionManager()

# Global instances for STT, VAD and TTS to avoid reloading models per connection
vad = SileroVADWrapper()
stt = FasterWhisperSTTWrapper()
tts = KokoroTTSWrapper()

def _pcm16_to_float32(pcm16_data: bytes) -> np.ndarray:
    """Convert raw PCM16 bytes to float32 numpy array for Silero/Whisper."""
    audio_int16 = np.frombuffer(pcm16_data, dtype=np.int16)
    audio_float32 = audio_int16.astype(np.float32) / 32768.0
    return audio_float32

def _float32_to_pcm16(float32_data: np.ndarray) -> bytes:
    """Convert float32 numpy array to PCM16 bytes."""
    audio_int16 = np.clip(float32_data * 32768.0, -32768, 32767).astype(np.int16)
    return audio_int16.tobytes()

def _resample_24k_to_16k(audio_float32: np.ndarray) -> np.ndarray:
    """Resample 24kHz audio from Kokoro to 16kHz for the consistent wire format."""
    return scipy.signal.resample_poly(audio_float32, 2, 3)

from typing import Optional, List, Any

def _safe_get_context(session: Any) -> Optional[Any]:
    if not session:
        return None
    if isinstance(session, dict):
        return session.get("context")
    return getattr(session, "context", None)

def _safe_get_current_question_id(session: Any) -> Optional[str]:
    context = _safe_get_context(session)
    if not context:
        return None
    if isinstance(context, dict):
        return context.get("current_question_id")
    return getattr(context, "current_question_id", None)

def _safe_get_history(session: Any) -> List[Any]:
    context = _safe_get_context(session)
    if not context:
        return []
    if isinstance(context, dict):
        topics = context.get("topics", {})
    else:
        topics = getattr(context, "topics", None)
    
    if not topics:
        return []
    
    if isinstance(topics, dict):
        return topics.get("history", [])
    return getattr(topics, "history", [])


MAX_BUFFER_SIZE_BYTES = 30 * 16000 * 2  # 30 seconds of 16kHz PCM16 (approx 960KB)

# Keep track of active connections to enforce session isolation (1 connection per session)
ACTIVE_SESSIONS = {}

class VoicePipelineSession:
    def __init__(self, websocket: WebSocket, session_id: str):
        self.ws = websocket
        self.session_id = session_id
        self.state = "IDLE"  # IDLE, LISTENING, CANDIDATE_SPEAKING, PROCESSING, INTERVIEWER_SPEAKING
        
        self.audio_buffer = bytearray()
        self.silence_chunks = 0
        self.is_connected = False
        self.expected_turn_id = None
        
        # Audio config
        self.chunk_duration_ms = 100
        self.sample_rate = 16000
        
        self.interruption_event = asyncio.Event()

    async def send_state(self, state: str):
        if self.state != state:
            logger.info(f"Session {self.session_id} state transition: {self.state} -> {state}")
            self.state = state
            try:
                await self.ws.send_json({"type": "state", "state": self.state})
            except:
                pass

    async def handle_candidate_speech_end(self):
        """Called when VAD detects candidate stopped speaking."""
        await self.send_state("PROCESSING")
        t0 = time.perf_counter()
        
        # 1. Convert accumulated buffer to float32
        audio_bytes = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        
        if len(audio_bytes) < self.sample_rate * 2: 
            # Less than 1 second of audio, likely noise
            logger.info("Audio too short, treating as noise and ignoring.")
            await self.send_state("LISTENING")
            return
            
        float32_audio = _pcm16_to_float32(audio_bytes)
        
        try:
            # 2. STT
            stt_t0 = time.perf_counter()
            result = await stt.transcribe(float32_audio)
            transcript = result.get("transcript", "").strip()
            logger.info(f"STT: {transcript} ({time.perf_counter()-stt_t0:.2f}s)")
            
            # Filter empty or hallucinatory transcripts
            if not transcript or transcript.lower() in ["[silence]", "[noise]", "thank you", "thanks"]:
                logger.info("Empty/hallucinated transcript, ignoring.")
                await self.send_state("LISTENING")
                return
                
            await self.ws.send_json({"type": "transcript", "text": transcript})
            
            # Idempotency / Duplicate Protection
            session = await session_mgr.get_or_restore_session(self.session_id)
            current_turn = _safe_get_current_question_id(session)
            if self.expected_turn_id and current_turn != self.expected_turn_id:
                logger.warning(f"Duplicate/Stale answer submission. Expected {self.expected_turn_id}, actual DB {current_turn}. Ignoring.")
                await self.send_state("LISTENING")
                return

            # Update local turn immediately to prevent overlapping duplicate submissions
            self.expected_turn_id = "PROCESSING_TURN"
            
            # 3. Evaluate / get next question
            eval_t0 = time.perf_counter()
            res = await session_mgr.submit_answer(self.session_id, transcript)
            logger.info(f"Evaluation took {time.perf_counter()-eval_t0:.2f}s")
            
            if res.is_completed:
                await self.ws.send_json({"type": "completion", "message": "Interview complete."})
                await self.send_state("COMPLETED")
                return
                
            next_question = res.next_question.question_text
            # Sync new turn ID for idempotency
            self.expected_turn_id = res.next_question.question_id

            await self.ws.send_json({"type": "question", "text": next_question})
            
            # 4. TTS
            await self.play_tts(next_question)
            
        except Exception as e:
            logger.error(f"Pipeline error (STT/Evaluation): {e}")
            await self.ws.send_json({"type": "error", "message": "Processing unavailable. Please try answering again.", "recoverable": True})
            await self.send_state("LISTENING")

    async def play_tts(self, text: str):
        """Stream TTS audio to the client, handling interruptions."""
        await self.send_state("INTERVIEWER_SPEAKING")
        self.interruption_event.clear()
        
        try:
            from api.config import DEV_MODE
            if DEV_MODE:
                await self.ws.send_json({"type": "dev_speak", "text": text})
                await asyncio.sleep(1.0)
                if self.state == "INTERVIEWER_SPEAKING":
                    await self.send_state("LISTENING")
                return

            # Signal TTS start
            await self.ws.send_json({"type": "interviewer_speech_start"})
            
            tts_gen = tts.speak_stream(text)
            async for float32_bytes in tts_gen:
                if self.interruption_event.is_set():
                    logger.info("TTS interrupted by candidate.")
                    break
                    
                audio_float32_24k = np.frombuffer(float32_bytes, dtype=np.float32)
                audio_float32_16k = _resample_24k_to_16k(audio_float32_24k)
                pcm16_bytes = _float32_to_pcm16(audio_float32_16k)
                
                try:
                    await self.ws.send_bytes(pcm16_bytes)
                except:
                    break
                    
            if not self.interruption_event.is_set():
                await self.ws.send_json({"type": "interviewer_speech_end"})
                
            # Safely transition to LISTENING unless we were interrupted to CANDIDATE_SPEAKING
            if self.state == "INTERVIEWER_SPEAKING":
                await self.send_state("LISTENING")
                
        except Exception as e:
            logger.error(f"TTS error: {e}")
            # Recovery: return to LISTENING so they can still answer
            if self.state == "INTERVIEWER_SPEAKING":
                await self.send_state("LISTENING")


@ws_router.websocket("/ws/interview/{session_id}/audio")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    
    # 1. Session Isolation & Validation
    if session_id in ACTIVE_SESSIONS:
        logger.warning(f"Duplicate connection attempt for session {session_id}")
        await websocket.send_json({"type": "error", "message": "Session already active on another connection."})
        await websocket.close(code=4001)
        return
        
    session = await session_mgr.get_or_restore_session(session_id)
    status = getattr(session, 'status', session.get('status') if isinstance(session, dict) else '')
    if not session or status == "completed":
        await websocket.send_json({"type": "error", "message": "Invalid or expired session."})
        await websocket.close(code=4001)
        return
        
    ACTIVE_SESSIONS[session_id] = websocket
    
    try:
        pipeline = VoicePipelineSession(websocket, session_id)
        pipeline.is_connected = True
        
        # Models are lazy-loaded on first use by each wrapper.
        # No eager preloading here — keeps connection setup fast,
        # and in DEV_MODE the stubs are used instead.
        
        # Reconnection State Recovery
        current_q = _safe_get_current_question_id(session)
        pipeline.expected_turn_id = current_q
        
        if current_q:
            # If there's an active question, emit it to the client to restore state
            q_text = "Please continue your interview."
            history = _safe_get_history(session)
            if history:
                for hist in reversed(history):
                    hist_q_id = getattr(hist, "question_id", hist.get("question_id") if isinstance(hist, dict) else None)
                    hist_q = getattr(hist, "question", hist.get("question") if isinstance(hist, dict) else None)
                    if hist_q_id == current_q and hist_q:
                        q_text = hist_q
                        break
            await websocket.send_json({"type": "question", "text": q_text})
            
        await pipeline.send_state("LISTENING")
        
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                pcm16_data = message["bytes"]
                
                # Malformed / Oversized chunks check
                if len(pcm16_data) % 2 != 0 or len(pcm16_data) > 64000:
                    continue

                if pipeline.state == "PROCESSING":
                    continue
                    
                is_interruption_check = pipeline.state == "INTERVIEWER_SPEAKING"
                
                float32_audio = _pcm16_to_float32(pcm16_data)
                is_speech = vad.is_speech(float32_audio)
                
                if is_interruption_check:
                    if is_speech:
                        pipeline.interruption_event.set()
                        await pipeline.send_state("CANDIDATE_SPEAKING")
                        pipeline.audio_buffer.extend(pcm16_data)
                        pipeline.silence_chunks = 0
                elif pipeline.state == "LISTENING":
                    if is_speech:
                        await pipeline.send_state("CANDIDATE_SPEAKING")
                        pipeline.audio_buffer.extend(pcm16_data)
                        pipeline.silence_chunks = 0
                elif pipeline.state == "CANDIDATE_SPEAKING":
                    pipeline.audio_buffer.extend(pcm16_data)
                    
                    # Backpressure / Buffer Limits
                    if len(pipeline.audio_buffer) > MAX_BUFFER_SIZE_BYTES:
                        logger.warning(f"Audio buffer exceeded max size {MAX_BUFFER_SIZE_BYTES} bytes. Forcing processing.")
                        asyncio.create_task(pipeline.handle_candidate_speech_end())
                        continue
                        
                    if not is_speech:
                        pipeline.silence_chunks += 1
                        if pipeline.silence_chunks > 15:
                            asyncio.create_task(pipeline.handle_candidate_speech_end())
                    else:
                        pipeline.silence_chunks = 0
                        
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "play_question":
                    # Let the frontend trigger the first question playback if needed
                    text = data.get("text", "")
                    if text and pipeline.state == "LISTENING":
                        asyncio.create_task(pipeline.play_tts(text))
                    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for session {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        pipeline.is_connected = False
        if session_id in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[session_id]
