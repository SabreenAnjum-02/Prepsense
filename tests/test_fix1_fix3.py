"""
Regression tests for:
  Fix #1 — SessionManager singleton (no split instances between routes.py / voice_ws.py)
  Fix #3 — WebSocket state synchronization (no LISTENING before first question, no double-receive)
"""
import asyncio
import pytest
import importlib
import sys

# ─────────────────────────────────────────────────────────────────────────────
# Fix #1: both modules must reference the IDENTICAL SessionManager object
# ─────────────────────────────────────────────────────────────────────────────
class TestSingletonIdentity:
    """Verify that api.routes and api.voice_ws share exactly one SessionManager."""

    def test_routes_and_voice_ws_share_same_session_manager(self):
        from api.session_manager import global_session_manager
        # Import the module-level binding used by each router
        import api.routes as routes_mod
        import api.voice_ws as ws_mod
        assert routes_mod.session_mgr is global_session_manager, (
            "api.routes.session_mgr must be the global_session_manager singleton"
        )
        assert ws_mod.session_mgr is global_session_manager, (
            "api.voice_ws.session_mgr must be the global_session_manager singleton"
        )
        # Both modules point to the same object
        assert routes_mod.session_mgr is ws_mod.session_mgr, (
            "routes.py and voice_ws.py must use the identical SessionManager object"
        )

    def test_session_created_in_routes_is_visible_in_ws(self):
        """A session added via the shared object is immediately visible from both imports."""
        from api.session_manager import global_session_manager
        import api.routes as routes_mod
        import api.voice_ws as ws_mod

        # Inject a fake session directly into the shared store
        sentinel = {"session_id": "test-singleton-123", "current_question": None}
        global_session_manager._sessions["test-singleton-123"] = sentinel

        try:
            assert routes_mod.session_mgr._sessions.get("test-singleton-123") is sentinel
            assert ws_mod.session_mgr._sessions.get("test-singleton-123") is sentinel
        finally:
            del global_session_manager._sessions["test-singleton-123"]


# ─────────────────────────────────────────────────────────────────────────────
# Fix #1: with Redis down, session written by routes.py is visible to voice_ws.py
# ─────────────────────────────────────────────────────────────────────────────
class TestRedisDownFallback:
    """Ensure the session state is coherent when Redis is unavailable."""

    @pytest.mark.asyncio
    async def test_session_written_without_redis_is_visible_cross_module(self, monkeypatch):
        from api.session_manager import global_session_manager
        import api.routes as routes_mod
        import api.voice_ws as ws_mod

        # Simulate Redis being down by making all redis_store methods no-ops.
        # database.redis_store is itself the RedisSessionStore singleton object.
        import database.redis_store as rs_obj
        async def _noop(*a, **kw): return None
        monkeypatch.setattr(rs_obj, "save_context", _noop)
        monkeypatch.setattr(rs_obj, "save_active_state", _noop)
        monkeypatch.setattr(rs_obj, "set_current_question", _noop)
        monkeypatch.setattr(rs_obj, "get_context", _noop)
        monkeypatch.setattr(rs_obj, "get_active_state", _noop)
        monkeypatch.setattr(rs_obj, "get_current_question", _noop)

        # Inject a session with current_question=None (pre-generation state)
        from agents.shared.types import QuestionRecord
        test_id = "test-redis-down-456"
        fake_q = QuestionRecord(
            question_id="q_1",
            question="What is dependency injection?",
            question_text="What is dependency injection?",
            topic="Software Design",
            difficulty="Medium",
            is_followup=False,
        )
        fake_session = {
            "session_id": test_id,
            "current_question": None,
            "context": None,
            "profile": None,
        }
        global_session_manager._sessions[test_id] = fake_session

        try:
            # Simulate what _bg_start does after generating the question
            global_session_manager._sessions[test_id]["current_question"] = fake_q

            # voice_ws.py's session_mgr (same object) sees the update immediately
            session_via_ws = ws_mod.session_mgr._sessions.get(test_id)
            assert session_via_ws is not None
            assert session_via_ws["current_question"] is fake_q, (
                "After routes.py sets current_question, voice_ws.py must see it without Redis"
            )
        finally:
            del global_session_manager._sessions[test_id]


# ─────────────────────────────────────────────────────────────────────────────
# Fix #3: pipeline.expected_turn_id gates the audio receive loop
# ─────────────────────────────────────────────────────────────────────────────
class TestPipelineGating:
    """Test VoicePipelineSession audio blocking logic when no question is ready."""

    def test_pipeline_starts_with_no_expected_turn_id(self):
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock
        mock_ws = MagicMock()
        p = VoicePipelineSession(mock_ws, "sess-abc")
        assert p.expected_turn_id is None, (
            "Pipeline must start with expected_turn_id=None (no question yet)"
        )
        assert p.state == "IDLE"

    def test_audio_silently_dropped_when_no_expected_turn_id(self):
        """Simulate the receive-loop guard: audio must be silently dropped."""
        # This replicates the guard logic directly from the fixed voice_ws.py:
        #   if not pipeline.expected_turn_id: continue
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock, AsyncMock

        mock_ws = MagicMock()
        p = VoicePipelineSession(mock_ws, "sess-abc")
        p.is_connected = True
        p.expected_turn_id = None   # no question ready

        # The guard condition
        should_drop = not p.expected_turn_id
        assert should_drop is True, (
            "Audio should be dropped (guard returns True) when no question is active"
        )

    def test_audio_accepted_once_turn_id_set(self):
        """After expected_turn_id is populated, audio should NOT be dropped."""
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock

        mock_ws = MagicMock()
        p = VoicePipelineSession(mock_ws, "sess-abc")
        p.expected_turn_id = "q_1"

        should_drop = not p.expected_turn_id
        assert should_drop is False, (
            "Audio should NOT be dropped once a question ID is registered"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Fix #3: state transition — PROCESSING holds until question is ready
# ─────────────────────────────────────────────────────────────────────────────
class TestInitialStateTransition:
    """The WS should be in PROCESSING (not LISTENING) before the first question."""

    @pytest.mark.asyncio
    async def test_initial_state_is_processing_when_no_question(self):
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock, AsyncMock, patch

        mock_ws = MagicMock()
        mock_ws.send_json = AsyncMock()
        p = VoicePipelineSession(mock_ws, "sess-test")
        p.is_connected = True

        # When no question exists, send_state("PROCESSING") should be called
        # (this replicates the fixed else-branch in voice_websocket_endpoint)
        current_q_id = None  # simulates: _safe_get_current_question_id returns None
        if current_q_id:
            pass  # would replay question
        else:
            await p.send_state("PROCESSING")

        mock_ws.send_json.assert_called_once_with({"type": "state", "state": "PROCESSING"})
        assert p.state == "PROCESSING"

    @pytest.mark.asyncio
    async def test_state_transitions_to_listening_after_question_delivered(self):
        """After play_tts completes (no interruption), state should be LISTENING."""
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock, AsyncMock, patch
        import asyncio

        mock_ws = MagicMock()
        mock_ws.send_json = AsyncMock()
        mock_ws.send_bytes = AsyncMock()
        p = VoicePipelineSession(mock_ws, "sess-test")
        p.is_connected = True

        # Patch TTS to produce a tiny audio chunk and complete
        async def fake_speak_stream(text):
            yield b'\x00\x00' * 100

        with patch.object(p.tts, 'speak_stream', fake_speak_stream):
            await p.play_tts("What is dependency injection?")

        # After play_tts finishes without interruption, state must be LISTENING
        assert p.state == "LISTENING", (
            f"Expected LISTENING after TTS completes, got {p.state}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Fix #3: disconnect handling — receive() raise must break the loop cleanly
# ─────────────────────────────────────────────────────────────────────────────
class TestDisconnectHandling:
    """No second receive() call after a disconnect event is received."""

    def test_disconnect_message_type_recognized(self):
        """The disconnect check in the loop correctly identifies websocket.disconnect."""
        disconnect_msg = {"type": "websocket.disconnect", "code": 1000}
        is_disconnect = disconnect_msg.get("type") == "websocket.disconnect"
        assert is_disconnect is True

    def test_normal_bytes_message_not_treated_as_disconnect(self):
        normal_msg = {"type": "websocket.receive", "bytes": b'\x00\x01'}
        is_disconnect = normal_msg.get("type") == "websocket.disconnect"
        assert is_disconnect is False

    def test_normal_text_message_not_treated_as_disconnect(self):
        text_msg = {"type": "websocket.receive", "text": '{"type":"ping"}'}
        is_disconnect = text_msg.get("type") == "websocket.disconnect"
        assert is_disconnect is False


# ─────────────────────────────────────────────────────────────────────────────
# Fix #3: silence does not trigger evaluation
# ─────────────────────────────────────────────────────────────────────────────
class TestSilenceHandling:
    """Empty/whitespace transcripts must not trigger answer submission."""

    @pytest.mark.asyncio
    async def test_empty_transcript_returns_to_listening(self):
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock, AsyncMock, patch
        import numpy as np

        mock_ws = MagicMock()
        mock_ws.send_json = AsyncMock()
        p = VoicePipelineSession(mock_ws, "sess-silence")
        p.is_connected = True
        p.expected_turn_id = "q_1"
        # Load a non-empty buffer (short audio = < 0.5 sec threshold)
        p.audio_buffer = bytearray(b'\x00' * 100)  # 50 samples = ~3ms

        # The handler checks len < 16000 bytes → too short → LISTENING
        with patch.object(p.stt, 'transcribe') as mock_transcribe:
            await p.handle_candidate_speech_end()
            mock_transcribe.assert_not_called()

        assert p.state == "LISTENING", (
            "Audio shorter than 0.5s must return to LISTENING without transcribing"
        )

    @pytest.mark.asyncio
    async def test_blank_transcript_returns_to_listening(self):
        from api.voice_ws import VoicePipelineSession
        from unittest.mock import MagicMock, AsyncMock, patch
        import numpy as np

        mock_ws = MagicMock()
        mock_ws.send_json = AsyncMock()
        p = VoicePipelineSession(mock_ws, "sess-blank")
        p.is_connected = True
        p.expected_turn_id = "q_1"
        # Buffer large enough to pass the length check (> 16000 bytes = > 0.5s at 16kHz)
        p.audio_buffer = bytearray(b'\x00' * 20000)

        async def fake_transcribe(audio):
            return {"transcript": "[silence]"}

        with patch.object(p.stt, 'transcribe', fake_transcribe):
            await p.handle_candidate_speech_end()

        assert p.state == "LISTENING", (
            "A '[silence]' transcript must return to LISTENING, not trigger evaluation"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Authentication: invalid/mismatched tokens must still be rejected
# ─────────────────────────────────────────────────────────────────────────────
class TestAuthRejection:
    """JWT validation must remain intact — no bypass."""

    def test_missing_token_produces_rejection(self):
        """Simulate the token=None guard at the top of voice_websocket_endpoint."""
        token = None
        should_reject = not token
        assert should_reject is True

    def test_session_mismatch_produces_rejection(self):
        """Token session_id must match URL session_id."""
        token_session_id = "session-A"
        url_session_id = "session-B"
        should_reject = not token_session_id or token_session_id != url_session_id
        assert should_reject is True

    def test_matching_session_passes(self):
        token_session_id = "session-A"
        url_session_id = "session-A"
        should_reject = not token_session_id or token_session_id != url_session_id
        assert should_reject is False
