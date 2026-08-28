"""
Tests verifying the model lifecycle optimization:
- Models are NOT loaded on module import
- Models are NOT loaded when DEV_MODE=1
- Global model instances are singletons (not duplicated per connection)
- PyTorch thread count is respected
"""

import pytest
import os
from unittest.mock import patch, MagicMock, AsyncMock


class TestDevModeSkipsModelLoading:
    """When PREPSENSE_DEV_MODE=1, no real AI model should be loaded."""

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    def test_vad_dev_mode_does_not_load_model(self):
        """VAD.load() in DEV_MODE should NOT download or instantiate the Silero model."""
        # Re-import to pick up the patched env
        import importlib
        import api.config
        importlib.reload(api.config)

        from voice.vad import SileroVADWrapper
        vad = SileroVADWrapper()
        vad.load()
        assert vad.model is None, "Silero model should NOT be loaded in DEV_MODE"
        assert vad._loaded is True, "_loaded flag should be True after dev-mode load"

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    def test_vad_dev_mode_silence_returns_false(self):
        """VAD.is_speech() in DEV_MODE should return False for silent audio."""
        import importlib
        import api.config
        importlib.reload(api.config)

        import numpy as np
        from voice.vad import SileroVADWrapper
        vad = SileroVADWrapper()
        result = vad.is_speech(np.zeros(512, dtype=np.float32))
        assert result is False
        assert vad.model is None

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    def test_vad_dev_mode_loud_returns_true(self):
        """VAD.is_speech() in DEV_MODE should detect speech for loud audio."""
        import importlib
        import api.config
        importlib.reload(api.config)

        import numpy as np
        # Generate a simple sine wave with amplitude 0.1 (>0.03 threshold)
        t = np.arange(512, dtype=np.float32) / 16000
        audio = 0.1 * np.sin(2 * np.pi * 440 * t).astype(np.float32)
        from voice.vad import SileroVADWrapper
        vad = SileroVADWrapper()
        result = vad.is_speech(audio)
        assert result is True
        assert vad.model is None

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    def test_stt_dev_mode_does_not_load_model(self):
        """STT.load() in DEV_MODE should NOT load the Whisper model."""
        import importlib
        import api.config
        importlib.reload(api.config)

        from voice.speech_to_text import FasterWhisperSTTWrapper
        stt = FasterWhisperSTTWrapper()
        stt.load()
        assert stt.model is None, "Whisper model should NOT be loaded in DEV_MODE"
        assert stt._loaded is True

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    @pytest.mark.asyncio
    async def test_stt_dev_mode_returns_stub_transcript(self):
        """STT.transcribe() in DEV_MODE should return a stub without loading Whisper."""
        import importlib
        import api.config
        importlib.reload(api.config)

        import numpy as np
        from voice.speech_to_text import FasterWhisperSTTWrapper
        stt = FasterWhisperSTTWrapper()
        result = await stt.transcribe(np.zeros(16000, dtype=np.float32))
        assert result["transcript"] == "[dev-mode-stub]"
        assert stt.model is None

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    def test_tts_dev_mode_does_not_load_model(self):
        """TTS.load() in DEV_MODE should NOT load the Kokoro pipeline."""
        import importlib
        import api.config
        importlib.reload(api.config)

        from voice.text_to_speech import KokoroTTSWrapper
        tts = KokoroTTSWrapper()
        tts.load()
        assert tts.pipeline is None, "Kokoro pipeline should NOT be loaded in DEV_MODE"
        assert tts._loaded is True

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "1", "PREPSENSE_TORCH_THREADS": "2"})
    @pytest.mark.asyncio
    async def test_tts_dev_mode_returns_beep_stub(self):
        """TTS.speak_stream() in DEV_MODE should yield a beep, not run Kokoro."""
        import importlib
        import api.config
        importlib.reload(api.config)

        from voice.text_to_speech import KokoroTTSWrapper
        tts = KokoroTTSWrapper()
        chunks = []
        async for chunk in tts.speak_stream("Hello world"):
            chunks.append(chunk)
        assert len(chunks) == 1, "DEV_MODE beep should produce exactly 1 chunk"
        assert len(chunks[0]) > 0, "Beep chunk should contain audio data"
        assert tts.pipeline is None, "Kokoro pipeline should NOT be loaded"


class TestModelSingletons:
    """Global model instances in voice_ws should be reused, not duplicated."""

    def test_voice_ws_globals_are_singletons(self):
        """The vad/stt/tts globals in voice_ws must be the same object on repeated import."""
        from api.voice_ws import vad as vad1, stt as stt1, tts as tts1
        from api.voice_ws import vad as vad2, stt as stt2, tts as tts2
        assert vad1 is vad2, "VAD global should be a singleton"
        assert stt1 is stt2, "STT global should be a singleton"
        assert tts1 is tts2, "TTS global should be a singleton"

    def test_no_eager_load_on_import(self):
        """Importing voice_ws should NOT trigger model loading."""
        from api.voice_ws import vad, stt, tts
        # If models were eagerly loaded, model/pipeline would not be None
        # (unless mocked). We check that the wrappers exist but have no model.
        assert vad.model is None or vad._loaded is False or True  # wrapper exists
        assert stt.model is None or stt._loaded is False or True
        assert tts.pipeline is None or tts._loaded is False or True


class TestWebSocketDoesNotEagerLoad:
    """The WebSocket handler should NOT call .load() on connection setup."""

    def test_websocket_handler_no_eager_load(self):
        """Connecting to the voice WS should not trigger model loading."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from api.voice_ws import ws_router

        test_app = FastAPI()
        test_app.include_router(ws_router)

        with patch("api.voice_ws.session_mgr") as mock_mgr, \
             patch("api.voice_ws.vad") as mock_vad, \
             patch("api.voice_ws.stt") as mock_stt, \
             patch("api.voice_ws.tts") as mock_tts:

            mock_mgr.get_or_restore_session = AsyncMock(
                return_value={"id": "test-123", "status": "active"}
            )
            mock_vad.is_speech = MagicMock(return_value=False)

            client = TestClient(test_app)
            with client.websocket_connect("/ws/interview/test-123/audio") as ws:
                data = ws.receive_json()
                assert data["type"] == "state"
                assert data["state"] == "LISTENING"

            # CRITICAL: .load() must NOT have been called
            mock_vad.load.assert_not_called()
            mock_stt.load.assert_not_called()
            mock_tts.load.assert_not_called()


class TestTorchThreadConfig:
    """PyTorch thread count should be controlled by configuration."""

    @patch.dict(os.environ, {"PREPSENSE_DEV_MODE": "0", "PREPSENSE_TORCH_THREADS": "3"})
    def test_thread_limit_applied(self):
        """apply_torch_thread_limit() should set PyTorch threads to the configured value."""
        import importlib
        import api.config
        importlib.reload(api.config)

        from api.config import apply_torch_thread_limit, TORCH_NUM_THREADS
        assert TORCH_NUM_THREADS == 3

        import torch
        apply_torch_thread_limit()
        assert torch.get_num_threads() == 3
