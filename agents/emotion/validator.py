from typing import Any
from agents.shared.types import EmotionAnalysisResult
from .utils import get_logger

logger = get_logger(__name__)

class EmotionValidator:
    """Validates inputs and outputs for the Emotion Analysis Agent."""

    @staticmethod
    def validate_input(video_frames: Any) -> bool:
        # In a real scenario, check if it's a valid list of frames or video object
        if not video_frames:
            logger.warning("Empty video input provided.")
            return False
        return True

    @staticmethod
    def validate_output(result: Any) -> bool:
        if not isinstance(result, EmotionAnalysisResult):
            logger.warning("Generated output is not a valid EmotionAnalysisResult.")
            return False
        return True
