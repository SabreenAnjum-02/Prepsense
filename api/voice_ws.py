import logging
import asyncio
import json
import numpy as np
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from api.session_manager import global_session_manager as session_mgr
from api.auth import SECRET_KEY, ALGORITHM
from voice.vad import SileroVADWrapper
from voice.speech_to_text import FasterWhisperSTTWrapper
from voice.text_to_speech import KokoroTTSWrapper
from jose import jwt, JWTError

logger = logging.getLogger(__name__)

ws_router = APIRouter()

ACTIVE_SESSIONS: Dict[str, WebSocket] = {}
ACTIVE_PIPELINES: Dict[str, Any] = {}

# Global singletons for voice models to avoid reloading on every websocket connection
global_vad = SileroVADWrapper()
global_stt = FasterWhisperSTTWrapper()
global_tts = KokoroTTSWrapper()

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
        
        self.vad = global_vad
        self.stt = global_stt
        self.tts = global_tts
        
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
                chunk_dur = len(audio_chunk) / (16000 * 2) 
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
            if res.next_question:
                self.expected_turn_id = res.next_question.question_id
                # ── Fix: Actually send the new question to the frontend! ──
                await self.ws.send_json({
                    "type": "question",
                    "text": res.next_question.question,
                    "question_id": res.next_question.question_id,
                    "stage": res.current_stage
                })
            else:
                self.expected_turn_id = None
            
            if getattr(res, 'is_completed', False) or res.current_stage == "CLOSING":
                await self.ws.send_json({"type": "completed"})
                if res.next_question:
                    await self.play_tts(res.next_question.question)
                return
                
            # Play AI's next question
            if res.next_question:
                asyncio.create_task(self.play_tts(res.next_question.question))
            
        except Exception as e:
            logger.error(f"[{self.session_id}] Pipeline error: {e}")
            await self.send_state("LISTENING")

def _safe_get_current_question_id(session: dict) -> Optional[str]:
    if not isinstance(session, dict):
        return None
    current_q = session.get("current_question")
    if current_q:
        if hasattr(current_q, "question_id"):
            return getattr(current_q, "question_id")
        elif isinstance(current_q, dict):
            return current_q.get("question_id")
        elif isinstance(current_q, str):
            return current_q

    context = session.get("context")
    if context:
        questions = getattr(context, "questions", None)
        if questions is None and isinstance(context, dict):
            questions = context.get("questions")
        if questions:
            last_q = questions[-1]
            return getattr(last_q, "question_id", None) or (last_q.get("question_id") if isinstance(last_q, dict) else None)
    return None

@ws_router.websocket("/ws/interview/{session_id}/audio")
async def voice_websocket_endpoint(websocket: WebSocket, session_id: str, token: str = Query(None)):
    if not token:
        logger.warning(f"WebSocket rejected for session {session_id}: Missing authentication token")
        await websocket.close(code=4001, reason="Missing authentication token")
        return
        
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        token_session_id = payload.get("session_id")
        if not email:
            logger.warning(f"WebSocket rejected for session {session_id}: Token missing sub claim")
            await websocket.close(code=4001, reason="Invalid token claims")
            return
        if not token_session_id or token_session_id != session_id:
            logger.warning(f"WebSocket rejected for session {session_id}: Token session mismatch (expected {session_id}, got {token_session_id})")
            await websocket.close(code=4001, reason="Token not valid for this session")
            return
    except JWTError as e:
        logger.warning(f"WebSocket rejected for session {session_id}: JWT error ({e})")
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    # Verify session exists and is active before accepting
    session = await session_mgr.get_or_restore_session(session_id)
    if not session:
        logger.warning(f"WebSocket rejected for session {session_id}: Session not found")
        await websocket.close(code=4001, reason="Session not found")
        return
        
    status = getattr(session, 'status', session.get('status') if isinstance(session, dict) else '')
    if status == "completed":
        logger.warning(f"WebSocket rejected for session {session_id}: Session already completed")
        await websocket.close(code=4001, reason="Session completed")
        return

    if session_id in ACTIVE_SESSIONS:
        logger.warning(f"Duplicate connection attempt for session {session_id}")
        await websocket.close(code=4001, reason="Session already active on another connection")
        return

    await websocket.accept()
    ACTIVE_SESSIONS[session_id] = websocket
    
    pipeline = VoicePipelineSession(websocket, session_id)
    pipeline.is_connected = True
    ACTIVE_PIPELINES[session_id] = pipeline
    
    try:
        # ── Fix #3: Set initial pipeline state based on whether a question already exists ──
        # When this WS connects BEFORE _bg_start() finishes generating Question 1,
        # current_question will be None. We send PROCESSING to hold the client in a
        # waiting state. We do NOT allow speech until expected_turn_id is populated.
        # When this WS reconnects AFTER a question already exists (e.g. session recovery),
        # we replay that question and begin TTS immediately.
        current_q = _safe_get_current_question_id(session)
        pipeline.expected_turn_id = current_q

        if pipeline.expected_turn_id:
            # Session reconnect: question already generated, replay it
            current_q_obj = session.get("current_question")
            q_text = getattr(current_q_obj, "question", None) if current_q_obj else None
            if not q_text and isinstance(current_q_obj, dict):
                q_text = current_q_obj.get("question")
            if not q_text:
                q_text = "Welcome back. Let's continue the interview."
            logger.info(f"[{session_id}] WS connected after question ready — replaying question.")
            await websocket.send_json({"type": "question", "text": q_text})
            asyncio.create_task(pipeline.play_tts(q_text))
        else:
            # First connect before _bg_start has finished: hold in PROCESSING
            # _bg_start() will send the question event and call play_tts once ready.
            logger.info(f"[{session_id}] WS connected — first question not yet ready. Holding in PROCESSING.")
            await pipeline.send_state("PROCESSING")
        
        # ── Main audio receive loop ──
        while True:
            try:
                message = await websocket.receive()
            except Exception as recv_exc:
                # receive() itself raised: connection is gone
                logger.info(f"[{session_id}] WebSocket receive raised: {recv_exc}")
                break

            # Starlette signals disconnect via a disconnect message type, not an exception
            if message.get("type") == "websocket.disconnect":
                logger.info(f"[{session_id}] WebSocket disconnect message received. Exiting loop.")
                break
            
            if "bytes" in message:
                pcm16_data = message["bytes"]
                
                if len(pcm16_data) % 2 != 0 or len(pcm16_data) > 64000:
                    continue

                # ── Fix #3 core: do NOT accept audio while no active question exists ──
                # This prevents silent/spurious audio from triggering evaluation when
                # the first question has not yet been delivered.
                if not pipeline.expected_turn_id:
                    # Still waiting for _bg_start() to populate the first question
                    continue

                if pipeline.state == "PROCESSING":
                    continue

                audio_np = np.frombuffer(pcm16_data, dtype=np.int16).astype(np.float32) / 32768.0
                is_speech_now = pipeline.vad.is_speech(audio_np)

                if pipeline.state == "INTERVIEWER_SPEAKING":
                    if is_speech_now:
                        pipeline.interruption_event.set()
                        await pipeline.send_state("CANDIDATE_SPEAKING")
                        pipeline.audio_buffer.clear()
                        pipeline.silence_chunks = 0
                    else:
                        continue

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
                            # State transition must happen synchronously before task scheduling
                            # to prevent multiple tasks from being spawned
                            pipeline.state = "PROCESSING"
                            asyncio.create_task(pipeline.handle_candidate_speech_end())
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
        logger.info(f"[{session_id}] WebSocket disconnected.")
    except Exception as e:
        logger.error(f"[{session_id}] WebSocket error: {e}")
    finally:
        pipeline.is_connected = False
        if session_id in ACTIVE_SESSIONS:
            del ACTIVE_SESSIONS[session_id]
        if session_id in ACTIVE_PIPELINES:
            del ACTIVE_PIPELINES[session_id]



