import logging
import asyncio
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

class FasterWhisperSTTWrapper:
    """Wrapper around Faster-Whisper for local Speech-to-Text."""
    
    def __init__(self, model_name: str = "base.en", compute_type: str = "default"):
        self.model_name = model_name
        self.compute_type = compute_type
        self.model = None
        self._loaded = False
        
    def load(self):
        """Lazily load the Faster-Whisper model."""
        if self._loaded:
            return

        from api.config import DEV_MODE, apply_torch_thread_limit
        apply_torch_thread_limit()

        if DEV_MODE:
            logger.info("DEV_MODE: Skipping Faster-Whisper model load.")
            self._loaded = True
            return

        if self.model is None:
            logger.info(f"Loading Faster-Whisper model ('{self.model_name}')...")
            try:
                # Use int8 compute type on CPU for lower memory usage and faster inference
                compute = self.compute_type
                if compute == "default":
                    compute = "int8"
                self.model = WhisperModel(self.model_name, device="cpu", compute_type=compute)
                self._loaded = True
                logger.info(f"Faster-Whisper model loaded successfully (compute_type={compute}).")
            except Exception as e:
                logger.error(f"Failed to load Faster-Whisper model: {e}")
                raise
                
    async def transcribe(self, audio_data) -> dict:
        """
        Transcribe the given audio data.
        audio_data: float32 numpy array of audio samples (16kHz mono).
        """
        from api.config import DEV_MODE
        if DEV_MODE:
            logger.info("DEV_MODE: Returning stub transcript.")
            return {
                "transcript": "[dev-mode-stub]",
                "language": "en",
                "language_probability": 1.0,
            }

        if self.model is None:
            self.load()
            
        logger.info("Transcribing audio chunk using Faster-Whisper...")
        
        try:
            # Faster-whisper can process numpy array directly
            # Run in a threadpool to prevent blocking the async event loop
            segments_gen, info = await asyncio.to_thread(self.model.transcribe, audio_data, beam_size=5)
            
            transcript = ""
            segments = list(segments_gen)
            for segment in segments:
                transcript += segment.text + " "
                
            return {
                "transcript": transcript.strip(),
                "language": info.language,
                "language_probability": info.language_probability
            }
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
