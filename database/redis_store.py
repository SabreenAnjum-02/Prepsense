import json
import logging
from typing import Optional, Dict, Any
from pydantic import BaseModel

from .config import db_config
from .connection import redis_manager
from agents.shared.types import InterviewContext, QuestionRecord

logger = logging.getLogger(__name__)


class RedisSessionStore:
    """Distributed Redis cache for fast active interview state reads/writes with TTL."""

    def __init__(self):
        self.ttl = db_config.redis.session_ttl_seconds

    def _state_key(self, session_id: str) -> str:
        return f"prepsense:session:{session_id}:state"

    def _context_key(self, session_id: str) -> str:
        return f"prepsense:session:{session_id}:context"

    def _question_key(self, session_id: str) -> str:
        return f"prepsense:session:{session_id}:current_q"

    async def save_active_state(self, session_id: str, state_data: Dict[str, Any]) -> bool:
        """Save high-level active session metadata into Redis."""
        client = await redis_manager.get_client()
        if not client:
            return False

        try:
            key = self._state_key(session_id)
            serialized = json.dumps(state_data, default=str)
            await client.set(key, serialized, ex=self.ttl)
            return True
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to save active state for {session_id}: {e}")
            return False

    async def get_active_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch active session state from Redis."""
        client = await redis_manager.get_client()
        if not client:
            return None

        try:
            key = self._state_key(session_id)
            raw = await client.get(key)
            if raw:
                return json.loads(raw)
            return None
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to get active state for {session_id}: {e}")
            return None

    async def save_context(self, session_id: str, context: InterviewContext) -> bool:
        """Cache full InterviewContext model in Redis."""
        client = await redis_manager.get_client()
        if not client:
            return False

        try:
            key = self._context_key(session_id)
            serialized = context.model_dump_json()
            await client.set(key, serialized, ex=self.ttl)
            return True
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to save context for {session_id}: {e}")
            return False

    async def get_context(self, session_id: str) -> Optional[InterviewContext]:
        """Fetch cached InterviewContext from Redis."""
        client = await redis_manager.get_client()
        if not client:
            return None

        try:
            key = self._context_key(session_id)
            raw = await client.get(key)
            if raw:
                data = json.loads(raw)
                return InterviewContext.model_validate(data)
            return None
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to get context for {session_id}: {e}")
            return None

    async def set_current_question(self, session_id: str, question: Optional[QuestionRecord]) -> bool:
        """Cache current active question in Redis."""
        client = await redis_manager.get_client()
        if not client:
            return False

        try:
            key = self._question_key(session_id)
            if question is None:
                await client.delete(key)
            else:
                serialized = question.model_dump_json()
                await client.set(key, serialized, ex=self.ttl)
            return True
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to set current question for {session_id}: {e}")
            return False

    async def get_current_question(self, session_id: str) -> Optional[QuestionRecord]:
        """Fetch current active question from Redis."""
        client = await redis_manager.get_client()
        if not client:
            return None

        try:
            key = self._question_key(session_id)
            raw = await client.get(key)
            if raw:
                return QuestionRecord.model_validate(json.loads(raw))
            return None
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to get current question for {session_id}: {e}")
            return None

    async def delete_session(self, session_id: str) -> bool:
        """Purge all Redis keys for a session."""
        client = await redis_manager.get_client()
        if not client:
            return False

        try:
            keys = [self._state_key(session_id), self._context_key(session_id), self._question_key(session_id)]
            await client.delete(*keys)
            return True
        except Exception as e:
            logger.warning(f"RedisSessionStore: Failed to delete session {session_id}: {e}")
            return False


redis_store = RedisSessionStore()
