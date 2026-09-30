import logging
import asyncio
import time
import json
import numpy as np
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from api.session_manager import SessionManager
from voice.vad import SileroVADWrapper
from voice.speech_to_text import FasterWhisperSTTWrapper
from voice.text_to_speech import KokoroTTSWrapper
import scipy.signal
from jose import jwt, JWTError
from api.auth import SECRET_KEY, ALGORITHM

logger = logging.getLogger(__name__)
ws_router = APIRouter()

session_mgr = SessionManager()
ACTIVE_SESSIONS = {}

class VoicePipelineSession:
    def __init__(self, websocket: WebSocket, session_id: str):
        self.ws = websocket
        self.session_id = session_id
        self.state = "IDLE"  
        
        self.audio_buffer = bytearray()
        self.silence_chunks = 0
        self.is_connected = False
        self.expected_turn_id = None
        
        # Audio config
        self.chunk_duration_ms = 100
        self.samples_per_chunk = int(16000 * (self.chunk_duration_ms / 1000.0))
        self.bytes_per_chunk = self.samples_per_chunk * 2 
        
        self.vad = SileroVADWrapper()
        self.stt = FasterWhisperSTTWrapper()
        self.tts = KokoroTTSWrapper()
        
        self.interruption_event = asyncio.Event()

    async def send_state(self, state: str):
        valid = ["IDLE", "LISTENING", "CANDIDATE_SPEAKING", "PROCESSING", "INTERVIEWER_SPEAKING"]
        if state not in valid:
            logger.error(f"Invalid state {state}")
            return
        self.state = state
        try:
            await self.ws.send_json({"type": "state", "state": self.state})
        except Exception as e:
            logger.error(f"Failed to send state: {e}")

    async def play_tts(self, text: str):
        if not text:
            return
        
        await self.send_state("PROCESSING")
        
        self.interruption_event.clear()
        
        logger.info(f"[{self.session_id}] TTS generation started: {text[:50]}...")
        await self.send_state("INTERVIEWER_SPEAKING")
        
        try:
            async for audio_chunk in self.tts.speak_stream(text):
                if self.interruption_event.is_set() or self.state == "CANDIDATE_SPEAKING":
                    logger.info(f"[{self.session_id}] Interrupted mid-TTS playback.")
                    break
                    
                if not self.is_connected:
                    break
                    
                await self.ws.send_bytes(audio_chunk)
                
                # simulate real-time playback delay so we can be interrupted
                chunk_dur = len(audio_chunk) / (24000 * 2) 
                await asyncio.sleep(chunk_dur * 0.9)
                
            if not self.interruption_event.is_set() and self.state == "INTERVIEWER_SPEAKING":
                await self.send_state("LISTENING")
                
        except Exception as e:
            logger.error(f"[{self.session_id}] TTS streaming failed: {e}")
            if self.state == "INTERVIEWER_SPEAKING" or self.state == "PROCESSING":
                await self.send_state("LISTENING")

    async def handle_candidate_speech_end(self):
        if not self.audio_buffer:
            await self.send_state("LISTENING")
            return
            
        await self.send_state("PROCESSING")
        
        pcm16_data = bytes(self.audio_buffer)
        self.audio_buffer.clear()
        
        # Too short to be real speech (e.g. mic bump)
        if len(pcm16_data) < 16000: # <0.5 sec
            await self.send_state("LISTENING")
            return

        audio_np = np.frombuffer(pcm16_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        try:
            stt_res = await self.stt.transcribe(audio_np)
            transcript = stt_res.get("transcript", "").strip()
            
            if not transcript or transcript.lower() in ["[silence]", "[blank]"]:
                await self.send_state("LISTENING")
                return
                
            logger.info(f"[{self.session_id}] Candidate said: {transcript}")
            await self.ws.send_json({"type": "transcript", "text": transcript})
            
            # Submit to AI
            res = await session_mgr.submit_answer(self.session_id, transcript)
            
            # Reset expected turn to the new question
            self.expected_turn_id = res.question_id
            
            if getattr(res, 'is_completed', False) or res.stage == "CLOSING":
                await self.ws.send_json({"type": "completed"})
                await self.play_tts(res.next_question.question)
                return
                
            # Play AI's next question
            asyncio.create_task(self.play_tts(res.next_question.question))
            
        except Exception as e:
            logger.error(f"[{self.session_id}] Pipeline error: {e}")
            await self.send_state("LISTENING")

def _safe_get_current_question_id(session: dict) -> str:
    current_q = session.get("current_question")
    if not current_q:
        hist = session.get("context", {}).get("topics", {}).get("history", [])
        if hist:
            current_q = hist[-1].question_id
    elif hasattr(current_q, "question_id"):
        return current_q.question_id
    elif isinstance(current_q, dict):
        return current_q.get("question_id")
    return current_q if isinstance(current_q, str) else None

@ws_router.websocket("/ws/interview/{session_id}/audio")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str, token: str = Query(None)):
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise JWTError()
    except JWTError:
        await websocket.close(code=4001, reason="Invalid authentication token")
        return

    await websocket.accept()
    
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
        
        current_q = _safe_get_current_question_id(session)
        pipeline.expected_turn_id = current_q
        
        if pipeline.expected_turn_id:
            q_text = "I'm ready. Let's continue."
            current_q_obj = session.get("current_question")
            if hasattr(current_q_obj, "question"):
                q_text = current_q_obj.question
            elif isinstance(current_q_obj, dict) and "question" in current_q_obj:
                q_text = current_q_obj["question"]
            else:
                hist = session.get("context", {}).get("topics", {}).get("history", [])
                for hist_q in hist:
                    hist_q_id = getattr(hist_q, "question_id", None) or (hist_q.get("question_id") if isinstance(hist_q, dict) else None)
                    if hist_q_id == current_q and hist_q:
                        q_text = hist_q
                        break
            await websocket.send_json({"type": "question", "text": q_text})
            
        await pipeline.send_state("LISTENING")
        
        while True:
            message = await websocket.receive()
            
            if "bytes" in message:
                pcm16_data = message["bytes"]
                
                if len(pcm16_data) % 2 != 0 or len(pcm16_data) > 64000:
                    continue

                if pipeline.state == "PROCESSING":
                    continue

                if pipeline.state == "INTERVIEWER_SPEAKING":
                    pipeline.interruption_event.set()
                    await pipeline.send_state("CANDIDATE_SPEAKING")
                    pipeline.audio_buffer.clear()
                    pipeline.silence_chunks = 0

                audio_np = np.frombuffer(pcm16_data, dtype=np.int16).astype(np.float32) / 32768.0
                is_speech_now = pipeline.vad.is_speech(audio_np)

                if is_speech_now:
                    if pipeline.state == "LISTENING":
                        await pipeline.send_state("CANDIDATE_SPEAKING")
                    pipeline.silence_chunks = 0
                    pipeline.audio_buffer.extend(pcm16_data)
                else:
                    if pipeline.state == "CANDIDATE_SPEAKING":
                        pipeline.audio_buffer.extend(pcm16_data)
                        pipeline.silence_chunks += 1
                        
                        if pipeline.silence_chunks > 15:
                            await pipeline.handle_candidate_speech_end()
                            pipeline.silence_chunks = 0
            
            elif "text" in message:
                data = json.loads(message["text"])
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "play_question":
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
