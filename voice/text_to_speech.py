import logging
import numpy as np
import os
import asyncio
import math

logger = logging.getLogger(__name__)

class KokoroTTSWrapper:
    """Wrapper around Kokoro TTS to generate and stream speech."""
    
    def __init__(self, voice: str = "af_bella"):
        self.voice = voice
        self.pipeline = None
        self.sample_rate = 24000
        self._loaded = False
        
    def load(self):
        """Lazily load the Kokoro pipeline."""
        if self._loaded:
            return

        from api.config import DEV_MODE, apply_torch_thread_limit
        apply_torch_thread_limit()

        if DEV_MODE:
            logger.info("DEV_MODE: Skipping Kokoro TTS model load.")
            self._loaded = True
            return

        if self.pipeline is None:
            logger.info(f"Loading Kokoro TTS model (voice={self.voice})...")
            try:
                # Import kokoro dynamically to allow graceful failure if not installed
                from kokoro import KPipeline
                self.pipeline = KPipeline(lang_code='a') # 'a' for American English
                self._loaded = True
                logger.info("Kokoro TTS model loaded successfully.")
            except ImportError:
                logger.error("Kokoro TTS not installed. Please install it via 'pip install kokoro'.")
                raise
            except Exception as e:
                logger.error(f"Failed to load Kokoro TTS: {e}")
                raise

    def _generate_dev_beep(self) -> np.ndarray:
        """Generate a short 440Hz sine wave beep (0.5s at 24kHz) for DEV_MODE."""
        duration = 0.5
        t = np.linspace(0, duration, int(self.sample_rate * duration), dtype=np.float32)
        # 440 Hz sine, tapered with a quick fade-in/out to avoid clicks
        beep = 0.3 * np.sin(2 * math.pi * 440 * t).astype(np.float32)
        fade_len = min(500, len(beep) // 4)
        beep[:fade_len] *= np.linspace(0, 1, fade_len, dtype=np.float32)
        beep[-fade_len:] *= np.linspace(1, 0, fade_len, dtype=np.float32)
        return beep

    async def speak_stream(self, text: str):
        """
        Convert text to speech and yield audio chunks as raw PCM Float32 bytes.
        
        In DEV_MODE, yields a short beep without loading any AI model.
        In production, runs Kokoro inference in a thread pool so it does not
        block the FastAPI async event loop.
        """
        from api.config import DEV_MODE

        if DEV_MODE:
            logger.info("DEV_MODE: Returning beep stub instead of Kokoro TTS.")
            beep = self._generate_dev_beep()
            yield beep.tobytes()
            return

        if self.pipeline is None:
            self.load()
            
        logger.info(f"Kokoro generating speech stream for text length {len(text)}")
        
        try:
            import time
            t0 = time.perf_counter()

            # Build the synchronous Kokoro generator on the calling thread.
            # Each next() call on it runs model inference and may block for
            # hundreds of milliseconds, so we pull chunks via to_thread().
            generator = self.pipeline(text, voice=self.voice, speed=1.0, split_pattern=r'\n+')
            
            first_chunk = True

            def _next_chunk():
                """Pull the next chunk from the synchronous Kokoro generator.
                Returns (gs, ps, audio) or None when exhausted."""
                try:
                    return next(generator)
                except StopIteration:
                    return None
            
            while True:
                # Run blocking Kokoro inference in a thread so the event loop
                # remains responsive to WebSocket pings, interruptions, etc.
                result = await asyncio.to_thread(_next_chunk)
                if result is None:
                    break

                gs, ps, audio = result
                if audio is not None:
                    if first_chunk:
                        logger.debug(f"TTS First chunk latency: {time.perf_counter() - t0:.2f}s")
                        first_chunk = False
                        
                    # audio is usually a torch tensor
                    if hasattr(audio, 'numpy'):
                        audio_np = audio.numpy()
                    else:
                        audio_np = audio
                        
                    # Yield raw Float32 bytes
                    yield audio_np.tobytes()
                    
        except Exception as e:
            logger.error(f"Kokoro TTS generation failed: {e}")
            raise
