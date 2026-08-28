from typing import Any
from .storage import StorageAdapter
from .repository import SessionRepository, ReportRepository
import logging

logger = logging.getLogger(__name__)

class DatabaseSession:
    """Manages transactions and repository access within a single context."""

    def __init__(self, storage: StorageAdapter):
        self.storage = storage
        self.sessions = SessionRepository(storage)
        self.reports = ReportRepository(storage)

    def begin(self) -> None:
        logger.info("DatabaseSession: Beginning transaction.")

    def commit(self) -> None:
        logger.info("DatabaseSession: Committing transaction.")

    def rollback(self) -> None:
        logger.info("DatabaseSession: Rolling back transaction.")

    def close(self) -> None:
        logger.info("DatabaseSession: Closing session.")
