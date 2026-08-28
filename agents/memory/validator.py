from typing import Any
from pydantic import ValidationError
from agents.shared.types import CandidateProfile, QuestionRecord, AnswerRecord, PerformanceRecord
from .utils import get_logger

logger = get_logger(__name__)

class MemoryValidator:
    """Validates records before they are committed to memory."""

    @staticmethod
    def validate_candidate_profile(data: Any) -> bool:
        if not isinstance(data, CandidateProfile):
            logger.warning("Invalid CandidateProfile object.")
            return False
        return True

    @staticmethod
    def validate_question(data: Any) -> bool:
        if not isinstance(data, QuestionRecord):
            logger.warning("Invalid QuestionRecord object.")
            return False
        return True

    @staticmethod
    def validate_answer(data: Any) -> bool:
        if not isinstance(data, AnswerRecord):
            logger.warning("Invalid AnswerRecord object.")
            return False
        return True

    @staticmethod
    def validate_performance(data: Any) -> bool:
        if not isinstance(data, PerformanceRecord):
            logger.warning("Invalid PerformanceRecord object.")
            return False
        return True
