import logging
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class InterviewSession:
    """Represents the data structure of an active interview session."""

    def __init__(self, session_id: str, candidate_name: str):
        self.session_id = session_id
        self.candidate_name = candidate_name
        self.started_at = datetime.now()
        self.ended_at: Optional[datetime] = None
        logger.info(f"InterviewSession: Created session {self.session_id} for {self.candidate_name}")

    def complete(self) -> None:
        self.ended_at = datetime.now()
        logger.info(f"InterviewSession: Session {self.session_id} marked as complete.")
