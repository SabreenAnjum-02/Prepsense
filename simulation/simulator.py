import logging
import asyncio
from typing import Any
from orchestrator.engine import AIOrchestrator
from orchestrator.router import AgentRouter
from orchestrator.state import OrchestratorState
from .mock_resume import get_mock_resume_path
from .mock_candidate import MockCandidate
from agents.shared.types import InterviewReport

logger = logging.getLogger(__name__)

class InterviewSimulator:
    """End-to-End Simulation Harness for PrepSense."""
    
    def __init__(self):
        # Instantiate the orchestrator with all core agents registered
        self.orchestrator = AIOrchestrator()
        self.candidate = MockCandidate()
        
        # Override the orchestrator pipeline execution slightly if we want to explicitly inject mock answers,
        # but since the orchestrator's pipeline.py ALREADY implements a [Mock Step] Simulating Candidate Answer,
        # we can just run the orchestrator as is.
        # However, to be fully faithful to this simulator's candidate, we would monkey-patch or inject the candidate.
        # For simplicity, we'll just run the standard orchestrator pipeline.

    async def run_simulation(self) -> InterviewReport:
        """Runs the complete simulated interview and returns the final report."""
        logger.info("==================================================")
        logger.info("InterviewSimulator: Starting End-to-End Simulation")
        logger.info("==================================================")
        
        # 1. Generate a mock resume PDF file path
        resume_path = get_mock_resume_path()
        logger.info(f"InterviewSimulator: Generated Mock Resume at {resume_path}")
        
        # 2. Execute Orchestrator Pipeline
        try:
            logger.info("InterviewSimulator: Handing off to AI Orchestrator...")
            # The AI Orchestrator handles the loop: Resume -> Memory -> Planner -> Interviewer -> Mock Answer -> Evaluator -> Memory -> Report
            final_report = await self.orchestrator.run_interview(resume_path)
            
            logger.info("==================================================")
            logger.info("InterviewSimulator: Simulation Completed Successfully")
            logger.info(f"Final Score: {final_report.overall_score}")
            logger.info(f"Hiring Decision: {final_report.hiring_decision}")
            logger.info("==================================================")
            
            return final_report
        except Exception as e:
            logger.error(f"InterviewSimulator: Simulation Failed: {e}")
            raise
