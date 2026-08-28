import logging
import time
from typing import Optional

from shared.config import VoiceConfig
from voice.models import AudioSessionState, VoiceResult
from voice.utils import time_tracker
from voice.validator import VoiceValidator
from voice.vad import SileroVADWrapper
from voice.speech_to_text import FasterWhisperSTTWrapper
from voice.text_to_speech import KokoroTTSWrapper
from voice.recorder import AudioRecorder

logger = logging.getLogger(__name__)

class VoiceService:
    """
    Public interface for the completely hands-free Voice Service.
    Orchestrates VAD, Recorder, STT, and TTS components natively.
    """
    
    def __init__(self, config: VoiceConfig):
        self.config = config
        self.state = AudioSessionState.IDLE
        
        # Validate configuration early
        VoiceValidator.validate_config(self.config)
        
        # Initialize internal components
        self.vad = SileroVADWrapper(sample_rate=self.config.sample_rate, threshold=self.config.vad_threshold)
        self.stt = FasterWhisperSTTWrapper(model_name=self.config.whisper_model_name)
        self.tts = KokoroTTSWrapper(voice=self.config.tts_voice)
        self.recorder = AudioRecorder(config=self.config, vad=self.vad)
        
        # Preload models (can be slow, but this is a singleton so it happens once)
        self._preload_models()
        
    def _preload_models(self):
        """Preload ML models into memory to reduce latency during interviews."""
        logger.info("Pre-loading VoiceService AI models...")
        self.vad.load()
        self.stt.load()
        self.tts.load()
        logger.info("VoiceService models loaded and ready.")
        
    def _set_state(self, state: AudioSessionState):
        """Update internal state and log the transition."""
        logger.debug(f"VoiceService state transition: {self.state.value} -> {state.value}")
        self.state = state

    async def speak(self, text: str) -> bool:
        """
        Convert text to speech and play it to the candidate.
        Returns True if successful.
        """
        self._set_state(AudioSessionState.SPEAKING_AI)
        try:
            with time_tracker(f"TTS Synthesis and Playback for {len(text)} chars"):
                await self.tts.speak(text)
            self._set_state(AudioSessionState.IDLE)
            return True
        except Exception as e:
            self._set_state(AudioSessionState.ERROR)
            logger.error(f"VoiceService.speak failed: {e}")
            return False

    async def listen_and_transcribe(self) -> VoiceResult:
        """
        Hands-free recording and transcription loop.
        Automatically waits for speech, records until silence, and transcribes.
        """
        result = VoiceResult()
        
        try:
            # 1. Listen
            self._set_state(AudioSessionState.WAITING_FOR_USER)
            start_record = time.time()
            
            audio_data = await self.recorder.listen_hands_free()
            
            end_record = time.time()
            result.audio_duration = end_record - start_record
            
            if len(audio_data) == 0:
                logger.warning("No speech detected or recording was too short.")
                result.success = False
                result.error_message = "No speech detected."
                self._set_state(AudioSessionState.IDLE)
                return result
                
            # 2. Transcribe
            self._set_state(AudioSessionState.PROCESSING)
            start_proc = time.time()
            
            with time_tracker("Speech-to-Text Transcription"):
                stt_result = await self.stt.transcribe(audio_data)
                
            end_proc = time.time()
            
            # 3. Compile Result
            result.transcript = stt_result.get("transcript", "")
            result.language = stt_result.get("language", "en")
            result.confidence = stt_result.get("language_probability", 0.0)
            result.processing_time = end_proc - start_proc
            result.success = True
            
            logger.info(f"Transcription complete: '{result.transcript}' (Conf: {result.confidence:.2f})")
            
        except Exception as e:
            self._set_state(AudioSessionState.ERROR)
            logger.error(f"VoiceService.listen_and_transcribe failed: {e}")
            result.success = False
            result.error_message = str(e)
        finally:
            self._set_state(AudioSessionState.IDLE)
            
        return result
