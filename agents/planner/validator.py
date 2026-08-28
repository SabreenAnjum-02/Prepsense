from typing import Any
from agents.shared.types import InterviewContext, InterviewPlan
from .utils import get_logger

logger = get_logger(__name__)

class PlannerValidator:
    """Validates inputs and outputs for the Planner Agent."""

    @staticmethod
    def validate_context(data: Any) -> bool:
        if not isinstance(data, InterviewContext):
            logger.warning("Invalid InterviewContext object provided to Planner.")
            return False
        return True

    @staticmethod
    def validate_plan(plan: Any) -> bool:
        if not isinstance(plan, InterviewPlan):
            logger.warning("Generated plan is not a valid InterviewPlan object.")
            return False
        return True
