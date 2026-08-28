from .candidate_memory import CandidateMemory
from .history import InterviewHistory
from .performance_memory import PerformanceMemory
from .utils import get_logger

logger = get_logger(__name__)


class SessionMemory:
    """Coordinates candidate, history, and performance memories for a single session."""

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.candidate = CandidateMemory()
        self.history = InterviewHistory()
        self.performance = PerformanceMemory()
        logger.info(f"Initialized SessionMemory for session ID: {session_id}")

    def clear(self) -> None:
        """Reset the entire session memory."""
        self.candidate.clear()
        self.history.clear()
        self.performance.clear()
        logger.info(f"Cleared SessionMemory for session ID: {self.session_id}")
