from typing import Any, List
from agents.shared.types import InterviewContext, EvaluationResult, InterviewReport
from .utils import get_logger

logger = get_logger(__name__)

class ReportValidator:
    """Validates inputs and outputs for the Report Agent."""

    @staticmethod
    def validate_inputs(context: Any, evaluations: Any) -> bool:
        if not isinstance(context, InterviewContext):
            logger.warning("Invalid InterviewContext object.")
            return False
        if not isinstance(evaluations, list) or not all(isinstance(e, EvaluationResult) for e in evaluations):
            logger.warning("Evaluations must be a list of EvaluationResult objects.")
            return False
        return True

    @staticmethod
    def validate_output(report: Any) -> bool:
        if not isinstance(report, InterviewReport):
            logger.warning("Generated output is not a valid InterviewReport.")
            return False
        return True
