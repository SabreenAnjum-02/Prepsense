from typing import List
from agents.shared.types import InterviewQuestion, AnswerRecord
from .utils import get_logger

logger = get_logger(__name__)

class FeedbackGenerator:
    """Generates qualitative feedback for an answer."""

    def identify_strengths(self, question: InterviewQuestion, answer: AnswerRecord) -> List[str]:
        """Placeholder for identifying strengths in the answer."""
        logger.info("Identifying strengths.")
        return ["Good initial approach.", "Clear communication tone."]

    def identify_weaknesses(self, question: InterviewQuestion, answer: AnswerRecord) -> List[str]:
        """Placeholder for identifying weaknesses in the answer."""
        logger.info("Identifying weaknesses.")
        return ["Lacked specific technical details.", "Missed edge cases."]

    def generate_suggestions(self, question: InterviewQuestion, answer: AnswerRecord) -> List[str]:
        """Placeholder for generating improvement suggestions."""
        logger.info("Generating improvement suggestions.")
        return ["Practice answering with the STAR method.", "Review core concepts of this topic."]
