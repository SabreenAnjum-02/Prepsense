import json
from typing import Optional, Any
from agents.shared.types import InterviewContext, InterviewPlan
from shared.llm.client import OllamaClient
from shared.llm.models import LLMRequest
from shared.error_handler import with_retry
from .utils import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)

class InterviewPlanner:
    """LLM-powered decision engine for the interview process."""

    def __init__(self, rag_service: Any = None) -> None:
        self.llm_client = OllamaClient()
        self.rag_service = rag_service

    @with_retry(max_retries=2, delay=1.0)
    async def plan_next_step(self, context: InterviewContext) -> Optional[InterviewPlan]:
        """Evaluate the context and plan the next step using the LLM."""
        logger.info("Planner evaluating next step via LLM.")
        
        # Retrieve context from RAG
        rag_context_str = ""
        if self.rag_service:
            # Create a query based on skills and previous questions
            skills = ", ".join(context.candidate_profile.skills) if context.candidate_profile and context.candidate_profile.skills else "software engineering"
            query = f"Interview topics and skills for {skills}"
            
            logger.info(f"Planner querying RAG: '{query}'")
            results = self.rag_service.query(query, top_k=2)
            
            if results:
                rag_context_str = "RETRIEVED KNOWLEDGE:\n"
                for res in results:
                    rag_context_str += f"- {res.chunk.content}\n"
                rag_context_str += "\n"
        
        prompt = (
            "You are the adaptive decision-making brain for a technical interview.\n"
            "Your job is to decide the next best step for the interview based on the current context.\n"
            "Analyze the candidate's profile, previous questions, performance, and coverage tracking.\n"
            f"{rag_context_str}"
            "DECISION RULES:\n"
            "- Decide ONE question at a time.\n"
            "- Ask at most 2-3 follow-up questions before changing topics.\n"
            "- Increase difficulty gradually if performance is good.\n"
            "- If performance is weak, simplify temporarily, then gradually increase difficulty again.\n"
            "- Cover all required interview categories according to the selected job role.\n"
            "- Balance interview depth with interview breadth.\n"
            "- Avoid spending too many questions on a single topic.\n"
            "- CRITICAL: Do NOT end the interview if the candidate has answered fewer than 5 questions or if coverage is incomplete.\n"
            "- End the interview only when sufficient evidence has been collected (based on topic coverage, confidence, and performance consistency).\n\n"
            "Return a strictly valid JSON object matching this structure:\n"
            "{\n"
            '  "next_topic": "string (or null if ending)",\n'
            '  "difficulty": "Easy, Medium, or Hard",\n'
            '  "objective": "string (e.g., Assess system design skills)",\n'
            '  "question_type": "string (e.g., Technical, Behavioral, System Design)",\n'
            '  "is_followup": boolean,\n'
            '  "interview_stage": "Must be exactly one of: INTRODUCTION, RESUME, TECHNICAL, PROJECTS, CODING, BEHAVIORAL, PSYCHOLOGICAL, GENERAL_KNOWLEDGE, HR, CLOSING",\n'
            '  "reason": "string (explaining why you chose this plan based on the rules)",\n'
            '  "should_end_interview": boolean\n'
            "}\n\n"
            f"INTERVIEW CONTEXT:\n{context.model_dump_json(indent=2)}\n"
        )
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are an expert technical interviewer planning the next question.",
            temperature=0.7,
            require_json=True
        )
        
        response = await self.llm_client.generate(request)
        
        if not response.parsed_json:
            logger.error("LLM failed to return valid JSON.")
            raise ValueError("Invalid JSON from LLM")
            
        try:
            plan = InterviewPlan(
                session_id=context.session_id,
                **response.parsed_json
            )
            return plan
        except ValidationError as e:
            logger.error(f"Planner LLM output failed validation: {e}")
            raise ValueError(f"Validation failed: {e}")
