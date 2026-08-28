from typing import Any
from agents.shared.types import InterviewContext, InterviewPlan, InterviewQuestion
from .utils import get_logger

logger = get_logger(__name__)

class InterviewerValidator:
    """Validates inputs and outputs for the Interviewer Agent."""

    @staticmethod
    def validate_inputs(context: Any, plan: Any) -> bool:
        if not isinstance(context, InterviewContext):
            logger.warning("Invalid InterviewContext object.")
            return False
        if not isinstance(plan, InterviewPlan):
            logger.warning("Invalid InterviewPlan object.")
            return False
        return True

    @staticmethod
    def validate_output(question: InterviewQuestion) -> bool:
        """Validate the generated InterviewQuestion."""
        if not isinstance(question, InterviewQuestion):
            return False
            
        if not question.question.strip():
            logger.error("Generated question text is empty.")
            return False
            
        return True
