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

        from api.config import DEV_MODE
        if DEV_MODE:
            # DEV_MODE: Lightweight RMS volume detection instead of loading Silero AI
            rms = np.sqrt(np.mean(audio_float32**2))
            # Lower threshold to 0.001 for quiet microphones
            if rms > 0.001:
                logger.debug(f'DEV_MODE VAD: Speech detected (RMS: {rms:.4f})')
                return True
            return False

        if not self._loaded:
            self.load()
            
        if len(audio_float32) == 0:
            return False
            
        # Convert to torch tensor
        tensor_chunk = torch.from_numpy(audio_float32).float()
        
        # Silero VAD model returns confidence
        # It requires exactly 512 samples per call (for 16000Hz)
        with torch.no_grad():
            chunk_size = 512
            for i in range(0, len(audio_float32), chunk_size):
                sub_chunk = audio_float32[i:i+chunk_size]
                if len(sub_chunk) < chunk_size:
                    # Pad the last chunk with zeros if it's too small
                    padded = np.zeros(chunk_size, dtype=np.float32)
                    padded[:len(sub_chunk)] = sub_chunk
                    sub_chunk = padded
                    
                tensor_chunk = torch.from_numpy(sub_chunk).float()
                speech_prob = self.model(tensor_chunk, self.sample_rate).item()
                if speech_prob >= self.threshold:
                    return True
            return False

