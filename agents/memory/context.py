from agents.shared.types import InterviewContext, InterviewStatistics
from .session_memory import SessionMemory
from .utils import get_logger

logger = get_logger(__name__)


class ContextBuilder:
    """Builds a comprehensive InterviewContext snapshot from SessionMemory."""

    @staticmethod
    def build(session: SessionMemory) -> InterviewContext:
        """Create a full context snapshot.

        Args:
            session: The active SessionMemory instance.

        Returns:
            An InterviewContext object representing the current state.
        """
        logger.info(f"Building InterviewContext snapshot for session ID: {session.session_id}")
        
        performance_records = session.performance.get_records()
        answers = session.history.get_answers()
        
        total_questions = len(performance_records)
        avg_tech = sum(r.technical_score for r in performance_records) / total_questions if total_questions > 0 else 0.0
        avg_comm = sum(r.communication_score for r in performance_records) / total_questions if total_questions > 0 else 0.0
        avg_conf = sum(r.confidence_score for r in performance_records) / total_questions if total_questions > 0 else 0.0
        duration = sum(a.time_taken_seconds for a in answers)
        
        stats = InterviewStatistics(
            total_questions=total_questions,
            average_technical_score=round(avg_tech, 2),
            average_communication_score=round(avg_comm, 2),
            average_confidence_score=round(avg_conf, 2),
            interview_duration_seconds=duration
        )
        
        return InterviewContext(
            session_id=session.session_id,
            candidate_profile=session.candidate.get_profile(),
            questions=session.history.get_questions(),
            answers=answers,
            performance=performance_records,
            topics=session.performance.get_topic_tracking(),
            statistics=stats,
            coverage=session.performance.get_coverage()
        )
