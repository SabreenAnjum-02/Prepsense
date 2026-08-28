import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from api.app import app
from api.voice_ws import ACTIVE_SESSIONS, VoicePipelineSession

@pytest.fixture
def mock_session_mgr():
    with patch("api.voice_ws.session_mgr") as mock_mgr:
        yield mock_mgr

@pytest.fixture
def mock_vad():
    with patch("api.voice_ws.vad") as mock_vad:
        mock_vad.is_speech.return_value = False
        yield mock_vad

@pytest.fixture
def mock_stt():
    with patch("api.voice_ws.stt") as mock_stt:
        mock_stt.transcribe = AsyncMock(return_value={"transcript": "test"})
        yield mock_stt

@pytest.fixture
def mock_tts():
    with patch("api.voice_ws.tts") as mock_tts:
        async def mock_stream(text):
            yield b"\x00" * 10
        mock_tts.speak_stream = mock_stream
        yield mock_tts

@pytest.mark.asyncio
async def test_ws_reconnect_state_recovery(mock_session_mgr):
    mock_session = MagicMock()
    mock_session.status = "active"
    mock_session.context.current_question_id = "q-3"
    hist = MagicMock()
    hist.question_id = "q-3"
    hist.question = "Can you explain REST?"
    mock_session.context.topics.history = [hist]
    mock_session_mgr.get_or_restore_session = AsyncMock(return_value=mock_session)
    
    client = TestClient(app)
    with client.websocket_connect("/api/ws/interview/test-sess-1/audio") as websocket:
        data1 = websocket.receive_json()
        data2 = websocket.receive_json()
        assert data1["type"] in ["question", "state"]
        assert data2["type"] in ["question", "state"]

from starlette.websockets import WebSocketDisconnect

def test_ws_duplicate_connection(mock_session_mgr):
    mock_session = MagicMock()
    mock_session.status = "active"
    mock_session_mgr.get_or_restore_session = AsyncMock(return_value=mock_session)
    client = TestClient(app)
    with client.websocket_connect("/api/ws/interview/test-duplicate/audio") as ws1:
        with client.websocket_connect("/api/ws/interview/test-duplicate/audio") as ws2:
            msg = ws2.receive_json()
            assert msg["type"] == "error"
            with pytest.raises(WebSocketDisconnect) as exc:
                ws2.receive_json()
            assert exc.value.code == 4001
        assert "test-duplicate" in ACTIVE_SESSIONS

def test_ws_cross_session_isolation():
    with patch("api.voice_ws.session_mgr.get_or_restore_session", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        client = TestClient(app)
        with client.websocket_connect("/api/ws/interview/invalid-sess/audio") as ws:
            msg = ws.receive_json()
            assert msg["type"] == "error"
            with pytest.raises(WebSocketDisconnect) as exc:
                ws.receive_json()
            assert exc.value.code == 4001

@pytest.mark.asyncio
async def test_ws_duplicate_answer_idempotency(mock_session_mgr, mock_vad, mock_stt):
    mock_session = MagicMock()
    mock_session.status = "active"
    mock_session.context.current_question_id = "q-4"
    mock_session_mgr.get_or_restore_session = AsyncMock(return_value=mock_session)
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    pipeline.expected_turn_id = "q-3"
    pipeline.audio_buffer.extend(b"\x00" * 32000)
    await pipeline.handle_candidate_speech_end()
    mock_session_mgr.submit_answer.assert_not_called()
    assert pipeline.state == "LISTENING"

@pytest.mark.asyncio
async def test_ws_tts_failure_recovery(mock_tts):
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    pipeline.state = "PROCESSING"
    async def mock_fail_stream(text):
        yield b"\x00"
        raise Exception("Kokoro TTS internal error")
    mock_tts.speak_stream = mock_fail_stream
    await pipeline.play_tts("Hello")
    assert pipeline.state == "LISTENING"

@pytest.mark.asyncio
async def test_ws_stt_failure_recovery(mock_stt):
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    pipeline.audio_buffer.extend(b"\x00" * 32000)
    mock_stt.transcribe.side_effect = Exception("Whisper STT error")
    await pipeline.handle_candidate_speech_end()
    assert pipeline.state == "LISTENING"

@pytest.mark.asyncio
async def test_ws_empty_noisy_audio(mock_stt):
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    pipeline.audio_buffer.extend(b"\x00" * 1000)
    await pipeline.handle_candidate_speech_end()
    mock_stt.transcribe.assert_not_called()
    assert pipeline.state == "LISTENING"
    
    pipeline.audio_buffer.extend(b"\x00" * 32000)
    mock_stt.transcribe.side_effect = None
    mock_stt.transcribe.return_value = {"transcript": "[silence]"}
    with patch("api.voice_ws.session_mgr.get_or_restore_session", new_callable=AsyncMock) as mock_sess:
        await pipeline.handle_candidate_speech_end()
        mock_sess.assert_not_called()
        assert pipeline.state == "LISTENING"

def test_ws_malformed_pcm(mock_session_mgr):
    mock_session = MagicMock()
    mock_session.status = "active"
    mock_session_mgr.get_or_restore_session = AsyncMock(return_value=mock_session)
    client = TestClient(app)
    with client.websocket_connect("/api/ws/interview/test-sess/audio") as ws:
        ws.send_bytes(b"\x00\x00\x00")
        assert "test-sess" in ACTIVE_SESSIONS

@pytest.mark.asyncio
async def test_ws_state_machine_validation():
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    await pipeline.send_state("LISTENING")
    assert pipeline.state == "LISTENING"

@pytest.mark.asyncio
async def test_ws_backpressure():
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    pipeline.state = "CANDIDATE_SPEAKING"
    pipeline.audio_buffer.extend(b"\x00" * (30 * 16000 * 2 + 10))

@pytest.mark.asyncio
async def test_ws_interruption():
    pipeline = VoicePipelineSession(AsyncMock(), "test-sess")
    
    async def mock_stream(text):
        # Simulate websocket loop changing the state mid-TTS
        pipeline.interruption_event.set()
        pipeline.state = "CANDIDATE_SPEAKING" 
        yield b"\x00" * 32000
        
    with patch("api.voice_ws.tts") as mock_tts:
        mock_tts.speak_stream = mock_stream
        await pipeline.play_tts("Hello")
    assert pipeline.state == "CANDIDATE_SPEAKING"

def test_ws_interview_completion(mock_session_mgr):
    mock_session = MagicMock()
    mock_session.status = "completed"
    mock_session_mgr.get_or_restore_session = AsyncMock(return_value=mock_session)
    client = TestClient(app)
    with client.websocket_connect("/api/ws/interview/test-sess/audio") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error"
        with pytest.raises(WebSocketDisconnect) as exc:
            ws.receive_json()
        assert exc.value.code == 4001
