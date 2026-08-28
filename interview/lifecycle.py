import logging
from .state import InterviewState, InterviewStateEnum
from .timer import InterviewTimer

logger = logging.getLogger(__name__)

class InterviewLifecycle:
    """Manages the transitions and events during the interview lifecycle."""

    def __init__(self, state: InterviewState, timer: InterviewTimer):
        self.state = state
        self.timer = timer

    def start(self) -> None:
        self.state.transition_to(InterviewStateEnum.IN_PROGRESS)
        self.timer.start()
        logger.info("InterviewLifecycle: Interview started.")

    def pause(self) -> None:
        if self.state.current_state == InterviewStateEnum.IN_PROGRESS:
            self.state.transition_to(InterviewStateEnum.PAUSED)
            self.timer.pause()
            logger.info("InterviewLifecycle: Interview paused.")
        else:
            logger.warning("InterviewLifecycle: Cannot pause. Not in progress.")

    def resume(self) -> None:
        if self.state.current_state == InterviewStateEnum.PAUSED:
            self.state.transition_to(InterviewStateEnum.IN_PROGRESS)
            self.timer.resume()
            logger.info("InterviewLifecycle: Interview resumed.")
        else:
            logger.warning("InterviewLifecycle: Cannot resume. Not paused.")

    def end(self) -> float:
        self.state.transition_to(InterviewStateEnum.COMPLETED)
        duration = self.timer.stop()
        logger.info(f"InterviewLifecycle: Interview ended. Final duration: {duration:.2f}s")
        return duration
