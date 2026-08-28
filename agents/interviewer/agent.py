from typing import Any, Optional
from agents.shared.base_agent import BaseAgent
from agents.shared.types import InterviewContext, InterviewPlan, InterviewQuestion
from .generator import QuestionGenerator
from .conversation import ConversationManager
from .validator import InterviewerValidator
from .utils import get_logger

logger = get_logger(__name__)


class InterviewerAgent(BaseAgent):
    """Generates natural interview questions based on the Planner's plan."""

    def __init__(
        self,
        generator: Optional[QuestionGenerator] = None,
        conversation_manager: Optional[ConversationManager] = None,
        rag_service: Any = None
    ) -> None:
        self._generator = generator or QuestionGenerator(rag_service=rag_service)
        self._conversation = conversation_manager or ConversationManager()
        self._validator = InterviewerValidator()

    @property
    def name(self) -> str:
        return "InterviewerAgent"

    async def run(self, input_data: Any) -> Optional[InterviewQuestion]:
        """Execute the question generation pipeline.

        Args:
            input_data: Expected to be a dict with 'context' and 'plan'.
                        'context' must be an InterviewContext.
                        'plan' must be an InterviewPlan.

        Returns:
            An InterviewQuestion object, or None if generation fails.
            
        Raises:
            ValueError: If input_data is invalid.
        """
        logger.info("InterviewerAgent invoked to generate a question.")

        if not isinstance(input_data, dict) or "context" not in input_data:
            raise ValueError("InterviewerAgent requires a dict with 'context'")

        context = input_data["context"]
        plan = input_data.get("plan")
        on_event = input_data.get("on_event")

        if plan and not self._validator.validate_inputs(context, plan):
            raise ValueError("Invalid inputs provided to InterviewerAgent.")

        # If a plan was explicitly provided and says end the interview, return early
        if plan and plan.should_end_interview:
            logger.info("Plan indicates the interview should end. Returning None.")
            return None

        max_attempts = 3
        question = None

        for attempt in range(max_attempts):
            # 1. Generate the question (stream only on first attempt to avoid duplicate TTS on retries)
            stream_cb = on_event if attempt == 0 else None
            question = await self._generator.generate_question(context, plan, on_event=stream_cb, attempt=attempt)

            if not question or question.should_end_interview:
                return question

            # 2. Format the question
            question = self._conversation.format_question(question)

            # 3. Check for duplicates
            if self._conversation.check_duplicate(context, question):
                logger.warning(f"Duplicate question detected on attempt {attempt + 1}/{max_attempts}. Retrying...")
                continue

            # 4. Validate output
            if self._validator.validate_output(question):
                logger.info(f"Successfully generated question for topic '{question.topic}'")
                return question
            else:
                logger.warning(f"Generated question failed validation on attempt {attempt + 1}/{max_attempts}.")

        # If retries exhausted but we have a valid question, return it
        if question and self._validator.validate_output(question):
            return question

        logger.error("Failed to generate a valid InterviewQuestion.")
        return None
