from typing import Any
from .audio_utils import get_logger

logger = get_logger(__name__)

class AudioCapture:
    """Handles routing audio streams from the frontend/microphone."""

    def start_stream(self) -> None:
        """Placeholder for starting an audio stream."""
        logger.info("Audio stream started.")

    def stop_stream(self) -> None:
        """Placeholder for stopping an audio stream."""
        logger.info("Audio stream stopped.")

    def get_chunk(self) -> bytes:
        """Placeholder for yielding the next chunk of raw audio."""
        logger.info("Captured raw audio chunk.")
        return b"mock_audio_data"
