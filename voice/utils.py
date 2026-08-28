import time
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

@contextmanager
def time_tracker(description: str, log_level: int = logging.INFO):
    """Context manager to track and log execution time."""
    start_time = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start_time
        logger.log(log_level, f"{description} took {elapsed:.3f} seconds.")
