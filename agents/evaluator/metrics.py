from agents.shared.types import EvaluationResult
from .utils import get_logger

logger = get_logger(__name__)

class MetricsCompiler:
    """Compiles individual scores and feedback into a finalized EvaluationResult."""

    def compile(
        self,
        question_id: str,
        tech_score: float,
        comm_score: float,
        prob_score: float,
        conf_score: float,
        overall_score: float,
        strengths: list,
        weaknesses: list,
        suggestions: list
    ) -> EvaluationResult:
        """Construct the final EvaluationResult object."""
        logger.info(f"Compiling evaluation result for question_id: {question_id}")
        
        return EvaluationResult(
            question_id=question_id,
            technical_score=tech_score,
            communication_score=comm_score,
            problem_solving_score=prob_score,
            confidence_score=conf_score,
            overall_score=overall_score,
            strengths=strengths,
            weaknesses=weaknesses,
            improvement_suggestions=suggestions
        )
