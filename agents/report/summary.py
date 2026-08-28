from typing import List
from agents.shared.types import InterviewContext, EvaluationResult
from .utils import get_logger

logger = get_logger(__name__)

class SummaryGenerator:
    """Generates the executive summary for the interview report."""

    def generate_final_summary(self, context: InterviewContext, evaluations: List[EvaluationResult], overall_score: float) -> str:
        """Create a written summary of the candidate's performance."""
        logger.info("Generating final summary text.")
        
        cand = context.candidate_profile
        name = cand.name if cand else "The candidate"
        
        if overall_score >= 0.8:
            return f"{name} demonstrated excellent proficiency across topics and communicated very effectively."
        elif overall_score >= 0.6:
            return f"{name} showed solid fundamental knowledge but had some gaps in complex areas."
        else:
            return f"{name} struggled to provide complete or accurate answers to the core topics."
