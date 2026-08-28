import logging
import asyncio
import numpy as np
import sounddevice as sd
import time
from shared.config import VoiceConfig
from voice.vad import SileroVADWrapper

logger = logging.getLogger(__name__)

class AudioRecorder:
    """Asynchronous audio recorder that integrates with VAD for hands-free listening."""
    
    def __init__(self, config: VoiceConfig, vad: SileroVADWrapper):
        self.config = config
        self.vad = vad
        
    async def listen_hands_free(self) -> np.ndarray:
        """
        Listens to the microphone automatically.
        Waits for speech to start, then records until silence timeout.
        Returns the recorded audio as a float32 numpy array.
        """
        logger.info("Starting hands-free recording session...")
        
        # Audio buffer
        recorded_chunks = []
        
        # State tracking
        has_started_speaking = False
        silence_start_time = None
        
        # Silero VAD requires exactly 512 samples at 16kHz or 256 at 8kHz
        chunk_samples = 512 if self.config.sample_rate == 16000 else 256
        
        loop = asyncio.get_running_loop()
        queue = asyncio.Queue()
        
        def audio_callback(indata, frames, time, status):
            if status:
                logger.warning(f"Audio callback status: {status}")
            # We copy because the indata buffer is reused by sounddevice
            loop.call_soon_threadsafe(queue.put_nowait, indata.copy())
            
        try:
            stream = sd.InputStream(
                samplerate=self.config.sample_rate,
                channels=self.config.recording_channels,
                dtype='float32',
                callback=audio_callback,
                blocksize=chunk_samples
            )
            
            with stream:
                start_time = time.time()
                
                while True:
                    # Enforce global max duration
                    if time.time() - start_time > self.config.max_recording_duration:
                        logger.warning("Max recording duration reached. Stopping.")
                        break
                        
                    # Get chunk from queue
                    chunk = await queue.get()
                    
                    # Flatten the (frames, channels) array to 1D
                    chunk_1d = chunk.flatten()
                    
                    # Check VAD
                    is_speech = self.vad.is_speech(chunk_1d)
                    
                    if not has_started_speaking:
                        if is_speech:
                            logger.info("Speech detected. Recording started.")
                            has_started_speaking = True
                            recorded_chunks.append(chunk_1d)
                    else:
                        recorded_chunks.append(chunk_1d)
                        
                        if is_speech:
                            # Reset silence timer
                            silence_start_time = None
                        else:
                            if silence_start_time is None:
                                silence_start_time = time.time()
                            elif time.time() - silence_start_time >= self.config.silence_timeout:
                                logger.info(f"Silence timeout ({self.config.silence_timeout}s) reached. Stopping.")
                                break
                                
        except sd.PortAudioError as e:
            logger.error(f"Microphone access failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during recording: {e}")
            raise
            
        if not recorded_chunks:
            return np.array([], dtype='float32')
            
        full_audio = np.concatenate(recorded_chunks)
        
        # Check if minimum duration was met
        total_duration = len(full_audio) / self.config.sample_rate
        if total_duration < self.config.minimum_speech_duration:
            logger.warning(f"Recording too short ({total_duration:.2f}s). Ignoring.")
            return np.array([], dtype='float32')
            
        return full_audio
