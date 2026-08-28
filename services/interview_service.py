import logging
from typing import Any, Optional
from agents.planner.agent import PlannerAgent
from agents.interviewer.agent import InterviewerAgent
from agents.memory.agent import MemoryAgent

logger = logging.getLogger(__name__)

class InterviewService:
    """Service to coordinate the core interview cycle between Planner, Interviewer, and Memory."""

    def __init__(self, planner_agent: PlannerAgent, interviewer_agent: InterviewerAgent, memory_agent: MemoryAgent):
        self.planner_agent = planner_agent
        self.interviewer_agent = interviewer_agent
        self.memory_agent = memory_agent

    async def advance_interview(self, session_id: str) -> Optional[Any]:
        """Coordinates the planning and question generation for the next step of the interview."""
        logger.info(f"InterviewService: Advancing interview for session {session_id}")
        
        # 1. Fetch current context from memory
        context = await self.memory_agent.run({
            "session_id": session_id,
            "action": "get_context"
        })
        
        if not context:
            logger.error("InterviewService: Failed to retrieve interview context.")
            return None

        # 2. Get plan from planner
        plan = await self.planner_agent.run({"context": context})
        
        if not plan or plan.should_end_interview:
            logger.info("InterviewService: Planner indicated the interview should end.")
            return None

        # 3. Generate question via interviewer
        question = await self.interviewer_agent.run({
            "context": context,
            "plan": plan
        })
        
        return question
