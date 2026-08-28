import time
import tracemalloc
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)

class PerformanceMetrics:
    """Stores performance statistics for a single interview session."""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time: float = time.perf_counter()
        self.end_time: float = 0.0
        self.total_execution_time: float = 0.0
        
        self.agent_latencies: Dict[str, list[float]] = {}
        self.failures: int = 0
        
        # Memory metrics (using Python's built-in tracemalloc)
        self.peak_memory_mb: float = 0.0
        
    def add_latency(self, agent_name: str, duration: float) -> None:
        if agent_name not in self.agent_latencies:
            self.agent_latencies[agent_name] = []
        self.agent_latencies[agent_name].append(duration)

    def record_failure(self) -> None:
        self.failures += 1

    def finalize(self) -> None:
        """Stops timers and memory tracing, and calculates final metrics."""
        self.end_time = time.perf_counter()
        self.total_execution_time = self.end_time - self.start_time
        
        # Capture memory usage
        if tracemalloc.is_tracing():
            current, peak = tracemalloc.get_traced_memory()
            self.peak_memory_mb = peak / (1024 * 1024)
            tracemalloc.stop()

    def generate_report(self) -> Dict[str, Any]:
        """Returns a structured dictionary of runtime statistics."""
        avg_latencies = {
            agent: sum(times) / len(times) 
            for agent, times in self.agent_latencies.items()
        }
        
        return {
            "session_id": self.session_id,
            "pipeline_execution_time_seconds": round(self.total_execution_time, 4),
            "peak_memory_mb": round(self.peak_memory_mb, 2),
            "total_failures": self.failures,
            "agent_average_latencies_seconds": {k: round(v, 4) for k, v in avg_latencies.items()}
        }

class SessionMonitor:
    """Centralized monitor for tracking interview session performance."""
    
    def __init__(self):
        self._sessions: Dict[str, PerformanceMetrics] = {}
        
    def start_session(self, session_id: str) -> None:
        """Initialize tracking for a new session."""
        logger.info(f"Monitor: Starting tracking for session {session_id}")
        tracemalloc.start()
        self._sessions[session_id] = PerformanceMetrics(session_id)

    def end_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Finalize tracking and return the statistical report."""
        if session_id in self._sessions:
            metrics = self._sessions[session_id]
            metrics.finalize()
            stats = metrics.generate_report()
            logger.info(f"Monitor: Session {session_id} stats finalized: {stats}")
            # Optionally clean up memory if we don't need to persist stats indefinitely
            return stats
        return None

    def record_agent_latency(self, session_id: str, agent_name: str, duration: float) -> None:
        """Log the execution duration of a specific agent."""
        if session_id in self._sessions:
            self._sessions[session_id].add_latency(agent_name, duration)

    def record_failure(self, session_id: str) -> None:
        """Increment the failure count for the session."""
        if session_id in self._sessions:
            self._sessions[session_id].record_failure()

# Global monitor instance
monitor = SessionMonitor()

def track_agent_latency(agent_name: str):
    """Decorator to automatically track an agent's run() execution latency."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args: Any, **kwargs: Any) -> Any:
            # Attempt to extract session_id from the standard BaseAgent payload dictionary
            session_id = None
            payload = args[0] if args else kwargs.get('input_data', {})
            if isinstance(payload, dict):
                session_id = payload.get("session_id")
            
            start_time = time.perf_counter()
            try:
                return await func(self, *args, **kwargs)
            except Exception:
                if session_id:
                    monitor.record_failure(session_id)
                raise
            finally:
                duration = time.perf_counter() - start_time
                if session_id:
                    monitor.record_agent_latency(session_id, agent_name, duration)
                logger.debug(f"Performance: Agent '{agent_name}' executed in {duration:.4f}s")
        return wrapper
    return decorator
