from typing import Any, Optional
from agents.shared.base_agent import BaseAgent
from agents.shared.types import InterviewContext, InterviewPlan
from .planner import InterviewPlanner
from .validator import PlannerValidator
from .utils import get_logger

logger = get_logger(__name__)


class PlannerAgent(BaseAgent):
    """The decision-making engine for the interview process.

    Analyzes the interview context to determine the next action for the interviewer.
    """

    def __init__(self, planner: Optional[InterviewPlanner] = None, rag_service: Any = None, decision_engine: Any = None, **kwargs) -> None:
        self._planner = planner or decision_engine or InterviewPlanner(rag_service=rag_service)
        self._validator = PlannerValidator()

    @property
    def name(self) -> str:
        return "PlannerAgent"

    async def run(self, input_data: Any) -> Optional[InterviewPlan]:
        """Process the interview context and generate an interview plan."""
        logger.info("PlannerAgent invoked to generate next step.")

        if hasattr(self._validator, "validate_input"):
            if not self._validator.validate_input(input_data):
                raise ValueError("Invalid input")

        if not isinstance(input_data, dict) or "context" not in input_data:
            raise ValueError("Invalid input: PlannerAgent requires a dict with 'context'")

        context = input_data["context"]

        if not self._validator.validate_context(context):
            raise ValueError("Invalid input: context validation failed.")

        # Generate the plan
        if hasattr(self._planner, "decide_next_step"):
            plan = self._planner.decide_next_step(context)
        else:
            plan = self._planner.plan_next_step(context)
            
        import inspect
        if inspect.isawaitable(plan):
            plan = await plan

        # Validate the output
        if not self._validator.validate_plan(plan):
            logger.error("Failed to generate a valid InterviewPlan.")
            return None

        logger.info(f"PlannerAgent successfully generated plan for session: {plan.session_id}")
        return plan
