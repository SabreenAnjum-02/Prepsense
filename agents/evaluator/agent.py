from typing import Any, Optional
from agents.shared.base_agent import BaseAgent
from agents.shared.types import EvaluationResult
from .llm_evaluator import LLMEvaluator
from .validator import EvaluatorValidator
from .utils import get_logger

logger = get_logger(__name__)


class EvaluatorAgent(BaseAgent):
    """Evaluates a candidate's response to an interview question."""

    def __init__(
        self,
        evaluator: Optional[Any] = None,
        rag_service: Any = None,
        scoring: Any = None,
        feedback: Any = None,
        metrics: Any = None,
        **kwargs
    ) -> None:
        self._evaluator = evaluator or LLMEvaluator(rag_service=rag_service)
        self._scoring = scoring
        self._metrics = metrics
        self._validator = EvaluatorValidator()

    @property
    def name(self) -> str:
        return "EvaluatorAgent"

    async def run(self, input_data: Any) -> Optional[EvaluationResult]:
        """Execute the evaluation pipeline."""
        logger.info("EvaluatorAgent invoked to evaluate an answer.")

        if hasattr(self._validator, "validate_input"):
            if not self._validator.validate_input(input_data):
                raise ValueError("Invalid input")

        if not isinstance(input_data, dict):
            raise ValueError("EvaluatorAgent requires a dictionary input.")

        req_keys = ["question", "answer", "context", "profile"]
        if not all(k in input_data for k in req_keys):
            raise ValueError(f"EvaluatorAgent input missing one of: {req_keys}")

        question = input_data["question"]
        answer = input_data["answer"]
        context = input_data["context"]
        profile = input_data["profile"]

        is_valid = True
        if hasattr(self._validator, "validate_inputs"):
            is_valid = self._validator.validate_inputs(question, answer, context, profile)
        if not is_valid:
            raise ValueError("Invalid inputs provided to EvaluatorAgent.")

        try:
            if self._metrics and hasattr(self._metrics, "compile"):
                result = self._metrics.compile()
            else:
                result = await self._evaluator.evaluate(question, answer, context, profile)

            # Validate output
            if not self._validator.validate_output(result):
                logger.error("Failed to generate a valid EvaluationResult.")
                return None

            logger.info(f"Successfully evaluated answer for question_id: {question.question_id}")
            return result

        except Exception as e:
            logger.error(f"Error during evaluation: {e}")
            raise
