import logging
from typing import Optional
from agents.shared.types import InterviewContext

logger = logging.getLogger(__name__)

class OrchestratorState:
    """Maintains the runtime state of the orchestrator."""
    def __init__(self):
        self.session_id: Optional[str] = None
        self.context: Optional[InterviewContext] = None
        self.is_running: bool = False
        self.error_count: int = 0

    def start_session(self, session_id: str) -> None:
        self.session_id = session_id
        self.is_running = True
        logger.info(f"OrchestratorState: Session {session_id} started.")

    def update_context(self, context: InterviewContext) -> None:
        self.context = context

    def terminate(self) -> None:
        self.is_running = False
        logger.info(f"OrchestratorState: Session {self.session_id} terminated.")
