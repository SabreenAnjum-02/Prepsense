from typing import Any
from agents.shared.types import InterviewContext, InterviewQuestion, AnswerRecord, CandidateProfile, EvaluationResult
from .utils import get_logger

logger = get_logger(__name__)

class EvaluatorValidator:
    """Validates inputs and outputs for the Evaluator Agent."""

    @staticmethod
    def validate_inputs(question: Any, answer: Any, context: Any, profile: Any) -> bool:
        if not isinstance(question, InterviewQuestion):
            logger.warning("Invalid InterviewQuestion object.")
            return False
        if not isinstance(answer, AnswerRecord):
            logger.warning("Invalid AnswerRecord object.")
            return False
        if not isinstance(context, InterviewContext):
            logger.warning("Invalid InterviewContext object.")
            return False
        if not isinstance(profile, CandidateProfile):
            logger.warning("Invalid CandidateProfile object.")
            return False
        return True

    @staticmethod
    def validate_output(result: Any) -> bool:
        if not isinstance(result, EvaluationResult):
            logger.warning("Generated output is not a valid EvaluationResult.")
            return False
        return True
