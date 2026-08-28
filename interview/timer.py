import time
import logging

logger = logging.getLogger(__name__)

class InterviewTimer:
    """Tracks the elapsed duration of the interview session."""

    def __init__(self):
        self.start_time: float = 0.0
        self.total_elapsed: float = 0.0
        self.is_running: bool = False

    def start(self) -> None:
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            logger.info("InterviewTimer: Started.")

    def pause(self) -> None:
        if self.is_running:
            self.total_elapsed += time.time() - self.start_time
            self.is_running = False
            logger.info("InterviewTimer: Paused.")

    def resume(self) -> None:
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            logger.info("InterviewTimer: Resumed.")

    def stop(self) -> float:
        if self.is_running:
            self.pause()
        logger.info(f"InterviewTimer: Stopped. Total duration: {self.total_elapsed:.2f}s")
        return self.total_elapsed

    def get_duration(self) -> float:
        if self.is_running:
            return self.total_elapsed + (time.time() - self.start_time)
        return self.total_elapsed
