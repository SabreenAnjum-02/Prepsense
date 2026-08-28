import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)

class InterviewStateEnum(Enum):
    INITIALIZED = "INITIALIZED"
    IN_PROGRESS = "IN_PROGRESS"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class InterviewState:
    """Manages the current state of an interview session."""

    def __init__(self):
        self.current_state: InterviewStateEnum = InterviewStateEnum.INITIALIZED
        self.question_count: int = 0
        self.progress_percentage: float = 0.0

    def transition_to(self, new_state: InterviewStateEnum) -> None:
        logger.info(f"InterviewState: Transitioning from {self.current_state.value} to {new_state.value}")
        self.current_state = new_state

    def increment_question(self, total_expected: int = 5) -> None:
        self.question_count += 1
        self.progress_percentage = min(100.0, (self.question_count / total_expected) * 100)
        logger.info(f"InterviewState: Progress updated to {self.progress_percentage}% ({self.question_count}/{total_expected})")
