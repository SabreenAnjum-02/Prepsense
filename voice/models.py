from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime

class AudioSessionState(str, Enum):
    IDLE = "IDLE"
    SPEAKING_AI = "SPEAKING_AI"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    LISTENING = "LISTENING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"

class VoiceResult(BaseModel):
    transcript: str = ""
    confidence: float = 0.0
    language: str = "en"
    audio_duration: float = 0.0
    speech_duration: float = 0.0
    silence_duration: float = 0.0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    ended_at: Optional[datetime] = None
    processing_time: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
