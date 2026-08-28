import logging
import asyncio
from functools import wraps
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)

class PrepSenseError(Exception):
    """Base exception for all internal application errors."""
    pass

class AgentExecutionError(PrepSenseError):
    """Raised when an agent fails to execute its core logic."""
    pass

class RetryableError(PrepSenseError):
    """Raised when an operation fails but can be safely retried (e.g. LLM timeout)."""
    pass

class TerminalError(PrepSenseError):
    """Raised when an operation fails and the session must be immediately aborted."""
    pass

def with_retry(max_retries: int = 3, delay: float = 1.0, exceptions=(RetryableError,)):
    """Decorator to automatically retry asynchronous operations upon transient failures."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_err = None
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_err = e
                    logger.warning(f"Attempt {attempt}/{max_retries} failed for {func.__name__}: {e}")
                    if attempt < max_retries:
                        await asyncio.sleep(delay)
            logger.error(f"All {max_retries} attempts failed for {func.__name__}. Operation aborted.")
            raise last_err
        return wrapper
    return decorator

class ErrorHandler:
    """Centralized service for catching, logging, and gracefully handling errors."""
    
    @staticmethod
    def handle_agent_failure(agent_name: str, exception: Exception, session_id: Optional[str] = None) -> dict:
        """
        Logs an agent failure and returns structured error information to bubble up.
        If a session_id is provided, the system gracefully logs the termination intent.
        """
        logger.error(f"ErrorHandler: Agent '{agent_name}' failed critically: {str(exception)}")
        
        if session_id:
            logger.error(f"ErrorHandler: Gracefully terminating session {session_id} due to fatal error in {agent_name}.")
            # In a robust system, we would publish a 'SessionFailed' event here via the EventBus
            # to alert the UI and Orchestrator state to freeze and dump logs.
            
        return {
            "error": True,
            "agent": agent_name,
            "message": str(exception),
            "type": type(exception).__name__,
            "recoverable": isinstance(exception, RetryableError)
        }
