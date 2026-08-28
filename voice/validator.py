from shared.config import VoiceConfig

class VoiceValidator:
    @staticmethod
    def validate_config(config: VoiceConfig):
        if config.silence_timeout <= 0:
            raise ValueError("silence_timeout must be > 0")
        if config.sample_rate not in (8000, 16000, 32000, 48000):
            raise ValueError("sample_rate must be a standard VAD rate (e.g., 16000)")
        if config.recording_channels != 1:
            raise ValueError("recording_channels must be 1 for VAD processing")
