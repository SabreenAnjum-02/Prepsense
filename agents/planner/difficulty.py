from typing import Optional
from agents.shared.types import InterviewContext
from .utils import get_logger

logger = get_logger(__name__)

class DifficultyAdjuster:
    """Decides the optimal difficulty level for the next question."""

    def select_difficulty(self, context: InterviewContext, is_followup: bool) -> str:
        """Determine whether the difficulty should be Easy, Medium, or Hard.

        Args:
            context: The current interview context.
            is_followup: True if the next question is a follow-up.

        Returns:
            The string representing the selected difficulty.
        """
        logger.info("Evaluating next question difficulty.")
        
        # Rolling multi-turn performance trend (average of last 2-3 records)
        if not context.performance:
            return "Medium"

        recent_records = context.performance[-3:]
        recent_scores = [r.overall_score if r.overall_score <= 1.0 else r.overall_score / 100.0 for r in recent_records]
        avg_score = sum(recent_scores) / len(recent_scores)
        latest_score = recent_scores[-1]

        # If it's a follow up to a poor answer, keep difficulty same or lower
        if is_followup and latest_score < 0.5:
            return "Easy"

        # Consistently strong (avg >= 75%) -> Hard
        if len(recent_scores) >= 2 and avg_score >= 0.75:
            return "Hard"
        elif len(recent_scores) >= 2 and avg_score < 0.40:
            return "Easy"
        elif latest_score >= 0.80 and len(recent_scores) == 1:
            return "Hard"
        elif latest_score < 0.40 and len(recent_scores) == 1:
            return "Easy"
        else:
            return "Medium"
