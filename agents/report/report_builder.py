from typing import List, Dict
from agents.shared.types import InterviewContext, EvaluationResult, InterviewReport
from .summary import SummaryGenerator
from .recommendations import RecommendationEngine
from .utils import get_logger

logger = get_logger(__name__)

class ReportBuilder:
    """Builds the final InterviewReport."""

    def __init__(
        self,
        summary: SummaryGenerator,
        recommendation: RecommendationEngine
    ) -> None:
        self._summary = summary
        self._rec = recommendation

    def _aggregate_strengths(self, evals: List[EvaluationResult]) -> List[str]:
        strengths = set()
        for e in evals:
            for s in e.strengths:
                strengths.add(s)
        return list(strengths)

    def _aggregate_weaknesses(self, evals: List[EvaluationResult]) -> List[str]:
        weaknesses = set()
        for e in evals:
            for w in e.weaknesses:
                weaknesses.add(w)
        return list(weaknesses)

    def _calculate_averages(self, evals: List[EvaluationResult]) -> tuple[float, float, float]:
        if not evals:
            return 0.0, 0.0, 0.0
        tech = sum(e.technical_score for e in evals) / len(evals)
        comm = sum(e.communication_score for e in evals) / len(evals)
        overall = sum(e.overall_score for e in evals) / len(evals)
        return tech, comm, overall

    def _calculate_topic_performance(self, context: InterviewContext, evals: List[EvaluationResult]) -> Dict[str, float]:
        # Maps question_id to topic
        q_map = {q.question_id: q.topic for q in context.questions}
        
        topic_scores = {}
        topic_counts = {}
        
        for e in evals:
            topic = q_map.get(e.question_id, "Unknown")
            topic_scores[topic] = topic_scores.get(topic, 0.0) + e.overall_score
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
            
        return {topic: topic_scores[topic] / topic_counts[topic] for topic in topic_scores}

    def build(self, context: InterviewContext, evaluations: List[EvaluationResult]) -> InterviewReport:
        """Construct the InterviewReport object."""
        logger.info("Building final InterviewReport.")

        tech_avg, comm_avg, overall_avg = self._calculate_averages(evaluations)
        topic_perf = self._calculate_topic_performance(context, evaluations)
        
        strengths = self._aggregate_strengths(evaluations)
        weaknesses = self._aggregate_weaknesses(evaluations)
        recommendations = self._rec.aggregate_recommendations(evaluations)
        
        hiring_decision = self._rec.determine_hiring_decision(overall_avg)
        final_summary = self._summary.generate_final_summary(context, evaluations, overall_avg)

        return InterviewReport(
            session_id=context.session_id,
            candidate_profile=context.candidate_profile,
            overall_score=overall_avg,
            technical_score=tech_avg,
            communication_score=comm_avg,
            topic_performance=topic_perf,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
            hiring_decision=hiring_decision,
            final_summary=final_summary
        )
