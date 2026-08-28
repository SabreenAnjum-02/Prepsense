import logging
from typing import Any
from .state import InterviewState
from .timer import InterviewTimer
from .lifecycle import InterviewLifecycle
from orchestrator.engine import AIOrchestrator

logger = logging.getLogger(__name__)

class InterviewSessionManager:
    """Manages the complete lifecycle and state of a single interview session."""

    def __init__(self, orchestrator: AIOrchestrator):
        self.orchestrator = orchestrator
        self.state = InterviewState()
        self.timer = InterviewTimer()
        self.lifecycle = InterviewLifecycle(self.state, self.timer)
        self.session_id = None

    def start_interview(self, resume_path: str) -> None:
        """Starts the interview and delegates execution to the Orchestrator."""
        logger.info(f"SessionManager: Starting interview with resume {resume_path}")
        self.lifecycle.start()
        # Note: In a fully asynchronous environment, this would be awaited or added to a task loop.
        # For this modular abstraction, we assume orchestrator is called.
        logger.info("SessionManager: Delegating to AI Orchestrator...")
        # await self.orchestrator.run_interview(resume_path)

    def pause_interview(self) -> None:
        """Pauses the active interview session."""
        self.lifecycle.pause()

    def resume_interview(self) -> None:
        """Resumes a paused interview session."""
        self.lifecycle.resume()

    def end_interview(self) -> dict:
        """Ends the interview and returns a summary of the session metadata."""
        final_duration = self.lifecycle.end()
        return {
            "duration_seconds": final_duration,
            "questions_asked": self.state.question_count,
            "progress_percentage": self.state.progress_percentage,
            "final_state": self.state.current_state.value
        }

    def record_question_asked(self, total_expected: int = 5) -> None:
        """Updates internal state when a new question is asked."""
        self.state.increment_question(total_expected)
