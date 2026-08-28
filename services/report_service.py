import logging
from typing import Any, Optional, List
from agents.report.agent import ReportAgent
from agents.memory.agent import MemoryAgent

logger = logging.getLogger(__name__)

class ReportService:
    """Service to coordinate the final report generation at the end of an interview."""

    def __init__(self, report_agent: ReportAgent, memory_agent: MemoryAgent):
        self.report_agent = report_agent
        self.memory_agent = memory_agent

    async def generate_final_report(self, session_id: str) -> Optional[Any]:
        """Coordinates fetching memory data and generating the final report."""
        logger.info(f"ReportService: Generating final report for session {session_id}")
        
        # 1. Fetch current context from memory
        context = await self.memory_agent.run({
            "session_id": session_id,
            "action": "get_context"
        })
        
        if not context:
            logger.error("ReportService: Failed to retrieve interview context.")
            return None

        # 2. Extract evaluations from the context
        # (Assuming the context contains performance records which we can pass as evaluations)
        # Note: In a fully wired system, we would map PerformanceRecords or EvaluationResults explicitly
        evaluations = context.performance if context.performance else []

        # 3. Generate report
        report = await self.report_agent.run({
            "context": context,
            "evaluations": evaluations
        })
        
        return report
