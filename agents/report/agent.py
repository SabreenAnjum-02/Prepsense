from typing import Any, Optional, List
from agents.shared.base_agent import BaseAgent
from agents.shared.types import InterviewReport, EvaluationResult
from .llm_report_generator import LLMReportGenerator
from .validator import ReportValidator
from .utils import get_logger

logger = get_logger(__name__)


class ReportAgent(BaseAgent):
    """Compiles the final interview report based on context and evaluations."""

    def __init__(
        self,
        generator: Optional[Any] = None,
        builder: Optional[Any] = None,
        **kwargs
    ) -> None:
        self._generator = generator or builder or LLMReportGenerator()
        self._validator = ReportValidator()

    @property
    def name(self) -> str:
        return "ReportAgent"

    async def run(self, input_data: Any) -> Optional[InterviewReport]:
        """Execute the report generation pipeline.

        Args:
            input_data: Expected to be a dict with:
                - 'context': InterviewContext
                - 'evaluations': List[EvaluationResult]

        Returns:
            An InterviewReport object, or None if generation fails.
            
        Raises:
            ValueError: If input_data is invalid.
        """
        logger.info("ReportAgent invoked to generate final report.")

        if not isinstance(input_data, dict):
            raise ValueError("ReportAgent requires a dictionary input.")

        req_keys = ["context", "evaluations"]
        if not all(k in input_data for k in req_keys):
            raise ValueError(f"ReportAgent input missing one of: {req_keys}")

        context = input_data["context"]
        evaluations = input_data["evaluations"]

        if not self._validator.validate_inputs(context, evaluations):
            raise ValueError("Invalid inputs provided to ReportAgent.")

        try:
            # 1. Build the report
            if hasattr(self._generator, "build"):
                report = self._generator.build(context, evaluations)
            else:
                report = self._generator.generate_report(context, evaluations)
                
            import inspect
            if inspect.isawaitable(report):
                report = await report

            # 2. Validate output
            if not self._validator.validate_output(report):
                logger.error("Failed to generate a valid InterviewReport.")
                return None

            logger.info(f"Successfully generated InterviewReport for session: {report.session_id}")
            return report

        except Exception as e:
            logger.error(f"Error during report generation: {e}")
            raise
