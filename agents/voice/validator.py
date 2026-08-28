from typing import Any
from agents.shared.types import VoiceAnalysisResult
from .utils import get_logger

logger = get_logger(__name__)

class VoiceValidator:
    """Validates inputs and outputs for the Voice Analysis Agent."""

    @staticmethod
    def validate_input(audio_input: Any) -> bool:
        # In a real scenario, check if it's a valid bytes object, filepath, or audio array
        if not audio_input:
            logger.warning("Empty audio input provided.")
            return False
        return True

    @staticmethod
    def validate_output(result: Any) -> bool:
        if not isinstance(result, VoiceAnalysisResult):
            logger.warning("Generated output is not a valid VoiceAnalysisResult.")
            return False
        return True
