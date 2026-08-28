from typing import Any, Dict, Optional, List
from agents.shared.base_agent import BaseAgent
from agents.shared.types import CandidateProfile, QuestionRecord, AnswerRecord, PerformanceRecord, InterviewContext
from .session_memory import SessionMemory
from .context import ContextBuilder
from .validator import MemoryValidator
from .utils import get_logger

logger = get_logger(__name__)


class MemoryAgent(BaseAgent):
    """Maintains the complete context and history of an interview session."""

    def __init__(self, session_memory=None, **kwargs) -> None:
        self._sessions: Dict[str, SessionMemory] = {}
        self._validator = MemoryValidator()
        self._injected_session_memory = session_memory

    @property
    def name(self) -> str:
        return "MemoryAgent"

    async def run(self, input_data: Any) -> Any:
        """Handle incoming requests to read/write memory."""
        if not isinstance(input_data, dict) or "action" not in input_data:
            raise ValueError("MemoryAgent requires a dict with 'action'")

        action = input_data["action"]
        session_id = input_data.get("session_id", "default_session")

        # Compatibility for tests expecting injected memory manager
        if action == "create_session" and self._injected_session_memory:
            return self._injected_session_memory.create_session()
        
        if action == "get_context" and self._injected_session_memory:
            return self._injected_session_memory.get_session(session_id)

        logger.info(f"MemoryAgent executing action '{action}' for session '{session_id}'")

        if action == "initialize_session":
            return self.initialize_session(session_id)
        
        valid_actions = [
            "store_candidate_profile", "add_question", "add_answer",
            "update_scores", "get_context", "get_previous_questions",
            "get_weak_topics", "get_strong_topics", "reset_session"
        ]
        
        if action not in valid_actions:
            raise ValueError(f"Unknown action: {action}")

        # All other actions require an initialized session
        session = self._sessions.get(session_id)
        if not session and not self._injected_session_memory:
            logger.error(f"Session {session_id} not initialized.")
            raise ValueError(f"Session {session_id} not initialized.")

        if action == "store_candidate_profile":
            return self.store_candidate_profile(session, payload=input_data.get("payload"))
        elif action == "add_question":
            return self.add_question(session, payload=input_data.get("payload"))
        elif action == "add_answer":
            return self.add_answer(session, payload=input_data.get("payload"))
        elif action == "update_scores":
            return self.update_scores(session, payload=input_data.get("payload"))
        elif action == "get_context":
            return self.get_context(session)
        elif action == "get_previous_questions":
            return self.get_previous_questions(session)
        elif action == "get_weak_topics":
            return self.get_weak_topics(session)
        elif action == "get_strong_topics":
            return self.get_strong_topics(session)
        elif action == "reset_session":
            return self.reset_session(session)
        else:
            raise ValueError(f"Unknown action: {action}")

    def initialize_session(self, session_id: str) -> bool:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionMemory(session_id)
        return True

    def store_candidate_profile(self, session: SessionMemory, payload: Any) -> bool:
        if self._validator.validate_candidate_profile(payload):
            session.candidate.store_profile(payload)
            return True
        return False

    def add_question(self, session: SessionMemory, payload: Any) -> bool:
        if self._validator.validate_question(payload):
            session.history.add_question(payload)
            session.performance.track_question(payload)
            return True
        return False

    def add_answer(self, session: SessionMemory, payload: Any) -> bool:
        if self._validator.validate_answer(payload):
            session.history.add_answer(payload)
            return True
        return False

    def update_scores(self, session: SessionMemory, payload: Any) -> bool:
        if self._validator.validate_performance(payload):
            session.performance.add_record(payload)
            # Update topics implicitly based on overall score heuristic
            # Standardize on 0-100 scale (>= 70.0 / 0.70 is strong, < 70.0 is weak)
            raw_score = payload.overall_score
            score = raw_score * 100.0 if raw_score <= 1.0 else raw_score
            is_strong = score >= 70.0
            
            question = next((q for q in session.history.get_questions() if q.question_id == payload.question_id), None)
            if question:
                session.performance.update_topic_tracking(question.topic, is_strong)
                logger.info(f"MemoryAgent: Tracked topic '{question.topic}' -> is_strong={is_strong} (score={score:.1f})")
            return True
        return False

    def get_context(self, session: SessionMemory) -> InterviewContext:
        return ContextBuilder.build(session)

    def get_previous_questions(self, session: SessionMemory) -> List[QuestionRecord]:
        return session.history.get_questions()

    def get_weak_topics(self, session: SessionMemory) -> List[str]:
        return session.performance.get_topic_tracking().weak_topics

    def get_strong_topics(self, session: SessionMemory) -> List[str]:
        return session.performance.get_topic_tracking().strong_topics

    def reset_session(self, session: SessionMemory) -> bool:
        session.clear()
        return True
