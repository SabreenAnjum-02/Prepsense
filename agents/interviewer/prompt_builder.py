from typing import Any
from agents.shared.types import InterviewContext, InterviewPlan
from .utils import get_logger

logger = get_logger(__name__)

class PromptBuilder:
    """Builds structured prompts to send to the LLM."""

    def build_prompt(self, context: InterviewContext, plan: InterviewPlan) -> str:
        """Combine the profile, context, and plan into a cohesive prompt.

        Args:
            context: The current state of the interview.
            plan: The planned next step.

        Returns:
            A string prompt ready for the LLM.
        """
        logger.info(f"Building LLM prompt for topic '{plan.next_topic}' and difficulty '{plan.difficulty}'")
        
        cand = context.candidate_profile
        candidate_info = f"Candidate: {cand.name if cand else 'Unknown'}\n"
        
        # In a real implementation, you would serialize context questions/answers
        # to ensure the LLM avoids duplicates and knows what was said.
        history_summary = f"Total previous questions asked: {len(context.questions)}\n"
        
        prompt = (
            "You are an expert technical interviewer.\n"
            f"{candidate_info}"
            f"Context: {history_summary}\n\n"
            "Your task is to generate ONE natural interview question based on the following plan:\n"
            f"- Topic: {plan.next_topic}\n"
            f"- Difficulty: {plan.difficulty}\n"
            f"- Type: {plan.question_type}\n"
            f"- Is Follow-up: {plan.is_followup}\n\n"
            "Respond ONLY with the question text. Do not include introductory text or pleasantries."
        )
        return prompt
