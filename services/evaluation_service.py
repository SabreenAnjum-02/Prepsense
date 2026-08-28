import logging
from typing import Any, Optional
from agents.evaluator.agent import EvaluatorAgent
from agents.memory.agent import MemoryAgent

logger = logging.getLogger(__name__)

class EvaluationService:
    """Service to coordinate the evaluation of candidate answers."""

    def __init__(self, evaluator_agent: EvaluatorAgent, memory_agent: MemoryAgent):
        self.evaluator_agent = evaluator_agent
        self.memory_agent = memory_agent

    async def evaluate_answer(self, session_id: str, question: Any, answer: Any) -> Optional[Any]:
        """Coordinates the evaluation of an answer and saving the result to memory."""
        logger.info(f"EvaluationService: Evaluating answer for session {session_id}")
        
        # 1. Fetch current context from memory
        context = await self.memory_agent.run({
            "session_id": session_id,
            "action": "get_context"
        })
        
        if not context:
            logger.error("EvaluationService: Failed to retrieve interview context.")
            return None

        # 2. Run evaluator
        result = await self.evaluator_agent.run({
            "question": question,
            "answer": answer,
            "context": context,
            "profile": context.candidate_profile
        })
        
        # 3. Store result back in memory (if successful)
        if result:
            await self.memory_agent.run({
                "session_id": session_id,
                "action": "update_scores",
                "payload": result
            })
            
        return result
