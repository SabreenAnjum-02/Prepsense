import logging
import torch
import numpy as np

logger = logging.getLogger(__name__)

class SileroVADWrapper:
    """Wrapper around Silero VAD to detect speech start/end."""
    
    def __init__(self, sample_rate: int = 16000, threshold: float = 0.5):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.model = None
        self.get_speech_timestamps = None
        self._loaded = False
        
    def load(self):
        """Lazily load the Silero VAD model."""
        if self._loaded:
            return

        from api.config import DEV_MODE, apply_torch_thread_limit
        apply_torch_thread_limit()

        if DEV_MODE:
            logger.info("DEV_MODE: Skipping Silero VAD model load.")
            self._loaded = True
            return

        if self.model is None:
            logger.info("Loading Silero VAD model...")
            try:
                # Load silero vad from torch hub
                self.model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                                                   model='silero_vad',
                                                   force_reload=False,
                                                   trust_repo=True)
                (self.get_speech_timestamps, _, _, _, _) = utils
                self._loaded = True
                logger.info("Silero VAD model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load Silero VAD: {e}")
                raise
                
    def is_speech(self, audio_float32: np.ndarray) -> bool:
        """Detect if the given audio chunk contains speech."""
        from api.config import DEV_MODE
        if DEV_MODE:
            import numpy as np
            # DEV_MODE: Lightweight RMS volume detection instead of loading Silero AI
            rms = np.sqrt(np.mean(audio_float32**2))
            return bool(rms > 0.005)

        if not self._loaded:
            self.load()
            
        if len(audio_float32) == 0:
            return False
            
        # Convert to torch tensor
        tensor_chunk = torch.from_numpy(audio_float32).float()
        
        # Silero VAD model returns confidence
        with torch.no_grad():
            speech_prob = self.model(tensor_chunk, self.sample_rate).item()
            
        return speech_prob >= self.threshold
