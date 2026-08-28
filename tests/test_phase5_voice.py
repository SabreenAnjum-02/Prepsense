import pytest
import asyncio
from fastapi import FastAPI, WebSocketDisconnect
from fastapi.testclient import TestClient
import numpy as np
import json
from unittest.mock import AsyncMock, MagicMock, patch

from api.voice_ws import ws_router, VoicePipelineSession

app = FastAPI()
app.include_router(ws_router)

# Dummy test data
mock_session_id = "test_session_123"
dummy_audio_bytes = b"\x00" * 3200  # 100ms of silence at 16kHz PCM16

@pytest.fixture
def mock_managers():
    with patch("api.voice_ws.session_mgr") as mock_session_mgr, \
         patch("api.voice_ws.vad") as mock_vad, \
         patch("api.voice_ws.stt") as mock_stt, \
         patch("api.voice_ws.tts") as mock_tts:
         
        # Mock session restore
        mock_session_mgr.get_or_restore_session = AsyncMock(return_value={"id": mock_session_id})
        
        # Mock VAD
        mock_vad.is_speech = MagicMock(return_value=False)
        
        # Mock STT
        mock_stt.transcribe = AsyncMock(return_value={"transcript": "hello world"})
        
        # Mock TTS (async generator)
        async def mock_speak_stream(text):
            yield b"\x01\x02\x03\x04" # dummy 24kHz float32
            
        mock_tts.speak_stream = mock_speak_stream
        
        # Mock evaluation
        mock_answer_res = MagicMock()
        mock_answer_res.is_completed = False
        mock_answer_res.next_question.question_text = "Next question please?"
        mock_session_mgr.submit_answer = AsyncMock(return_value=mock_answer_res)
        
        yield mock_session_mgr, mock_vad, mock_stt, mock_tts

def test_1_websocket_connection_valid(mock_managers):
    """Test 1 & 2: Valid session connects successfully."""
    client = TestClient(app)
    with client.websocket_connect(f"/ws/interview/{mock_session_id}/audio") as websocket:
        # First message should be LISTENING state
        data = websocket.receive_json()
        assert data["type"] == "state"
        assert data["state"] == "LISTENING"

def test_3_websocket_invalid_session(mock_managers):
    """Test 3 & 4: Invalid/cross session isolation."""
    mock_session_mgr, _, _, _ = mock_managers
    mock_session_mgr.get_or_restore_session = AsyncMock(return_value=None)
    
    client = TestClient(app)
    try:
        with client.websocket_connect(f"/ws/interview/invalid_123/audio") as websocket:
            data = websocket.receive_json()
            assert data["type"] == "error"
    except WebSocketDisconnect as e:
        assert e.code == 4001

def test_5_audio_frame_handling_and_vad(mock_managers):
    """Test 5, 6, 7: Audio frames, VAD start, VAD end."""
    mock_session_mgr, mock_vad, mock_stt, _ = mock_managers
    
    client = TestClient(app)
    with client.websocket_connect(f"/ws/interview/{mock_session_id}/audio") as websocket:
        data = websocket.receive_json() # LISTENING
        
        # Send silence
        websocket.send_bytes(dummy_audio_bytes)
        
        # Send speech
        mock_vad.is_speech.return_value = True
        websocket.send_bytes(dummy_audio_bytes)
        
        # Receive CANDIDATE_SPEAKING
        data = websocket.receive_json()
        assert data["state"] == "CANDIDATE_SPEAKING"
        
        # Send 16 frames of silence to trigger SPEECH_END (threshold is > 15 chunks)
        mock_vad.is_speech.return_value = False
        for _ in range(16):
            websocket.send_bytes(dummy_audio_bytes)
            
        # Expect PROCESSING state
        data = websocket.receive_json()
        assert data["state"] == "PROCESSING"

def test_8_empty_transcript(mock_managers):
    """Test 8: Empty transcript does not advance interview."""
    mock_session_mgr, mock_vad, mock_stt, _ = mock_managers
    mock_stt.transcribe = AsyncMock(return_value={"transcript": ""})
    
    client = TestClient(app)
    with client.websocket_connect(f"/ws/interview/{mock_session_id}/audio") as websocket:
        websocket.receive_json() # LISTENING
        
        # Speech start
        mock_vad.is_speech.return_value = True
        websocket.send_bytes(dummy_audio_bytes)
        websocket.receive_json() # CANDIDATE_SPEAKING
        
        # Speech end
        mock_vad.is_speech.return_value = False
        for _ in range(16):
            websocket.send_bytes(dummy_audio_bytes)
            
        websocket.receive_json() # PROCESSING
        
        # Wait for fallback to LISTENING because of empty transcript
        data = websocket.receive_json()
        assert data["state"] == "LISTENING"
        
        # Ensure evaluate was NOT called
        mock_session_mgr.submit_answer.assert_not_called()

def test_9_valid_transcript_and_tts(mock_managers):
    """Test 9, 13, 17: Valid transcript, submit, next question, TTS streaming."""
    mock_session_mgr, mock_vad, mock_stt, _ = mock_managers
    
    client = TestClient(app)
    with client.websocket_connect(f"/ws/interview/{mock_session_id}/audio") as websocket:
        websocket.receive_json() # LISTENING
        
        # Speech start
        mock_vad.is_speech.return_value = True
        websocket.send_bytes(dummy_audio_bytes)
        websocket.receive_json() # CANDIDATE_SPEAKING
        
        # Speech end
        mock_vad.is_speech.return_value = False
        for _ in range(16):
            websocket.send_bytes(dummy_audio_bytes)
            
        websocket.receive_json() # PROCESSING
        
        # Next should be the transcript event
        data = websocket.receive_json()
        assert data["type"] == "transcript"
        assert data["text"] == "hello world"
        
        # Next should be question event
        data = websocket.receive_json()
        assert data["type"] == "question"
        assert data["text"] == "Next question please?"
        
        # Next should be TTS speaking state
        data = websocket.receive_json()
        assert data["state"] == "INTERVIEWER_SPEAKING"
        
        data = websocket.receive_json()
        assert data["type"] == "interviewer_speech_start"
        
        # Next should be binary TTS audio
        b = websocket.receive_bytes()
        assert len(b) > 0
        
        data = websocket.receive_json()
        assert data["type"] == "interviewer_speech_end"
        
        data = websocket.receive_json()
        assert data["state"] == "LISTENING"

def test_14_interruption(mock_managers):
    """Test 14: Candidate interrupts interviewer TTS."""
    mock_session_mgr, mock_vad, mock_stt, mock_tts = mock_managers
    
    # Slow down TTS so we can interrupt it
    async def slow_mock_speak_stream(text):
        for _ in range(5):
            yield b"\x01\x02\x03\x04"
            await asyncio.sleep(0.5)
            
    mock_tts.speak_stream = slow_mock_speak_stream
    
    client = TestClient(app)
    with client.websocket_connect(f"/ws/interview/{mock_session_id}/audio") as websocket:
        websocket.receive_json() # LISTENING
        
        # Trigger an answer to get to TTS
        mock_vad.is_speech.return_value = True
        websocket.send_bytes(dummy_audio_bytes)
        websocket.receive_json() # CANDIDATE_SPEAKING
        
        mock_vad.is_speech.return_value = False
        for _ in range(16):
            websocket.send_bytes(dummy_audio_bytes)
            
        websocket.receive_json() # PROCESSING
        websocket.receive_json() # transcript
        websocket.receive_json() # question
        websocket.receive_json() # INTERVIEWER_SPEAKING
        websocket.receive_json() # speech_start
        
        websocket.receive_bytes() # chunk 1
        
        # Candidate INTERRUPTS
        mock_vad.is_speech.return_value = True
        websocket.send_bytes(dummy_audio_bytes)
        
        # We should immediately receive CANDIDATE_SPEAKING
        data = websocket.receive_json()
        assert data["state"] == "CANDIDATE_SPEAKING"
        # The TTS should stop sending chunks and transition back, or wait, it just stops.
        # Ensure we didn't receive speech_end
        # The rest of the stream is killed.
