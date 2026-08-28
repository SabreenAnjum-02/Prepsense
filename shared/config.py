import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ModelConfig(BaseModel):
    provider: str = Field(default_factory=lambda: os.getenv("MODEL_PROVIDER", "ollama"))
    model_name: str = Field(default_factory=lambda: os.getenv("MODEL_NAME", "qwen3:8b"))
    temperature: float = Field(default_factory=lambda: float(os.getenv("MODEL_TEMPERATURE", "0.7")))
    max_tokens: int = Field(default_factory=lambda: int(os.getenv("MODEL_MAX_TOKENS", "2000")))

class LoggingConfig(BaseModel):
    level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = Field(default_factory=lambda: os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    file_path: Optional[str] = Field(default_factory=lambda: os.getenv("LOG_FILE_PATH", None))

class FeatureFlags(BaseModel):
    enable_voice: bool = Field(default_factory=lambda: os.getenv("FEATURE_VOICE", "false").lower() == "true")
    enable_emotion: bool = Field(default_factory=lambda: os.getenv("FEATURE_EMOTION", "false").lower() == "true")
    enable_mock_mode: bool = Field(default_factory=lambda: os.getenv("FEATURE_MOCK_MODE", "false").lower() == "true")

class VoiceConfig(BaseModel):
    silence_timeout: float = Field(default_factory=lambda: float(os.getenv("VOICE_SILENCE_TIMEOUT", "4.5")))
    sample_rate: int = Field(default_factory=lambda: int(os.getenv("VOICE_SAMPLE_RATE", "16000")))
    recording_channels: int = Field(default_factory=lambda: int(os.getenv("VOICE_RECORDING_CHANNELS", "1")))
    max_recording_duration: float = Field(default_factory=lambda: float(os.getenv("VOICE_MAX_RECORDING_DURATION", "120.0")))
    minimum_speech_duration: float = Field(default_factory=lambda: float(os.getenv("VOICE_MIN_SPEECH_DURATION", "0.5")))
    whisper_model_name: str = Field(default_factory=lambda: os.getenv("VOICE_WHISPER_MODEL", "base.en"))
    tts_voice: str = Field(default_factory=lambda: os.getenv("VOICE_TTS_VOICE", "af_bella"))
    vad_threshold: float = Field(default_factory=lambda: float(os.getenv("VOICE_VAD_THRESHOLD", "0.4")))

class BaseConfig(BaseModel):
    """Base configuration supporting environment variables."""
    environment: str = "default"
    model: ModelConfig = Field(default_factory=ModelConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    features: FeatureFlags = Field(default_factory=FeatureFlags)
    voice: VoiceConfig = Field(default_factory=VoiceConfig)

class DevelopmentConfig(BaseConfig):
    environment: str = "development"
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self.logging.level = os.getenv("LOG_LEVEL", "DEBUG")
        self.features.enable_mock_mode = os.getenv("FEATURE_MOCK_MODE", "true").lower() == "true"

class TestingConfig(BaseConfig):
    environment: str = "testing"
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self.logging.level = os.getenv("LOG_LEVEL", "CRITICAL")
        self.features.enable_mock_mode = True
        self.model.provider = "mock"

class ProductionConfig(BaseConfig):
    environment: str = "production"
    
    def __init__(self, **data: Any):
        super().__init__(**data)
        self.logging.level = os.getenv("LOG_LEVEL", "WARNING")
        self.features.enable_mock_mode = False

def get_config() -> BaseConfig:
    """Factory function to get the configuration based on the PREPSENSE_ENV variable."""
    env = os.getenv("PREPSENSE_ENV", "development").lower()
    
    if env == "production":
        return ProductionConfig()
    elif env == "testing":
        return TestingConfig()
    else:
        return DevelopmentConfig()

# Global configuration instance
config = get_config()
