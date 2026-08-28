from typing import List
from agents.shared.types import EvaluationResult
from .utils import get_logger

logger = get_logger(__name__)

class RecommendationEngine:
    """Generates the hiring decision and final recommendations."""

    def determine_hiring_decision(self, overall_score: float) -> str:
        """Decide the final hiring recommendation based on score."""
        logger.info("Determining hiring decision.")
        if overall_score >= 0.85:
            return "Strong Hire"
        elif overall_score >= 0.70:
            return "Hire"
        elif overall_score >= 0.60:
            return "Weak Hire"
        else:
            return "No Hire"

    def aggregate_recommendations(self, evaluations: List[EvaluationResult]) -> List[str]:
        """Aggregate suggestions from individual evaluations."""
        logger.info("Aggregating improvement recommendations.")
        recs = set()
        for eval_res in evaluations:
            for r in eval_res.improvement_suggestions:
                recs.add(r)
        return list(recs)
