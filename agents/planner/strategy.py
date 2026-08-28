from agents.shared.types import InterviewContext
from .utils import get_logger

logger = get_logger(__name__)

class InterviewStrategy:
    """Determines the overarching strategy and question type."""

    def select_question_type(self, context: InterviewContext, topic: str, is_followup: bool) -> str:
        """Decide if the next question should be Technical, Behavioural, HR, etc.

        Args:
            context: The current interview context.
            topic: The selected topic.
            is_followup: True if it's a follow-up.

        Returns:
            The string representing the question type.
        """
        logger.info(f"Selecting question type for topic: {topic}")
        
        # Simple heuristic
        if is_followup:
            return "Follow-up"
        
        if topic.lower() in ["leadership", "teamwork", "conflict resolution"]:
            return "Behavioural"
            
        if topic.lower() in ["salary", "culture", "availability"]:
            return "HR"
            
        return "Technical"
