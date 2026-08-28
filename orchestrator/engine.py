import logging
from typing import Any, Optional
from .router import AgentRouter
from .state import OrchestratorState
from .pipeline import InterviewPipeline
from shared.container import container, setup_container

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """The central engine coordinating all AI Agents for PrepSense."""

    def __init__(self):
        self.router = AgentRouter()
        self.state = OrchestratorState()
        self.pipeline = InterviewPipeline(self.router, self.state)
        
        # Ensure container is populated before resolving
        setup_container()
        self._register_default_agents()

    def _register_default_agents(self) -> None:
        """Resolve all core agents from the DI container and register them into the router."""
        logger.info("AIOrchestrator: Resolving agents from DI container.")
        
        self.router.register_agent("resume", container.resolve("resume_agent"))
        self.router.register_agent("memory", container.resolve("memory_agent"))
        self.router.register_agent("planner", container.resolve("planner_agent"))
        self.router.register_agent("interviewer", container.resolve("interviewer_agent"))
        self.router.register_agent("evaluator", container.resolve("evaluator_agent"))
        self.router.register_agent("report", container.resolve("report_agent"))
        
        logger.info("AIOrchestrator: Agent registration complete.")

    async def run_interview(self, resume_path: str, target_role: Optional[str] = None, target_jd: Optional[str] = None) -> Any:
        """Trigger the complete interview process."""
        logger.info("AIOrchestrator: Triggered run_interview")
        return await self.pipeline.execute(resume_path, target_role=target_role, target_jd=target_jd)
