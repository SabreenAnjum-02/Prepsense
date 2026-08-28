from agents.shared.types import InterviewContext
from .utils import get_logger

logger = get_logger(__name__)

class FollowupAnalyzer:
    """Determines whether a follow-up question is needed based on previous answers."""

    def needs_followup(self, context: InterviewContext) -> bool:
        """Analyze the latest performance to decide if a follow-up is warranted.

        Args:
            context: The current interview context.

        Returns:
            True if a follow-up is needed, False otherwise.
        """
        logger.info("Analyzing if a follow-up is required.")
        
        if not context.performance:
            return False
            
        latest_perf = context.performance[-1]
        raw_score = latest_perf.overall_score
        score = raw_score / 100.0 if raw_score > 1.0 else raw_score
        
        raw_conf = latest_perf.confidence_score
        conf = raw_conf / 100.0 if raw_conf > 1.0 else raw_conf
        
        # Follow up if the answer was mediocre/incomplete or if they lacked confidence
        if 0.4 <= score <= 0.7:
            logger.info("Answer score implies follow-up needed for clarity.")
            return True
            
        if conf < 0.6:
            logger.info("Candidate lacked confidence. Follow-up to prompt for detail.")
            return True
            
        return False
