import logging
from typing import Any
from agents.resume.agent import ResumeAgent

logger = logging.getLogger(__name__)

class ResumeService:
    """Service to coordinate the Resume Agent."""

    def __init__(self, resume_agent: ResumeAgent):
        self.resume_agent = resume_agent

    async def process_resume(self, file_path: str) -> Any:
        """Coordinates the parsing and extraction of a candidate profile from a resume."""
        logger.info(f"ResumeService: Processing resume from {file_path}")
        input_data = {"file_path": file_path}
        profile = await self.resume_agent.run(input_data)
        return profile
