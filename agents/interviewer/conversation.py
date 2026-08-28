from agents.shared.types import InterviewContext, InterviewQuestion
from .utils import get_logger
import re

logger = get_logger(__name__)

class ConversationManager:
    """Manages the conversation tone, formatting, and redundancy checks."""

    def format_question(self, question: InterviewQuestion) -> InterviewQuestion:
        """Format the question text to ensure a professional tone.

        Args:
            question: The generated question.

        Returns:
            The formatted question.
        """
        text = question.question or ""
        # Clean up multiple trailing question marks / periods
        text = text.rstrip('.? ')
        text += '?'
            
        # Clean up weird LLM artifacts
        text = re.sub(r'^\s*(Question|Interviewer):\s*', '', text, flags=re.IGNORECASE)
        
        question.question = text.strip()
        return question

    def check_duplicate(self, context: InterviewContext, question: InterviewQuestion) -> bool:
        """Check if the generated question is too similar to a previously asked one.

        Args:
            context: The current interview context.
            question: The newly generated question.

        Returns:
            True if it's a duplicate, False otherwise.
        """
        if not context.questions or not question.question:
            return False

        logger.info("Checking for duplicate questions.")
        
        q_text = question.question.strip().lower()
        
        # Stopwords to filter out for keyword overlap comparison
        stopwords = {
            "what", "is", "are", "the", "a", "an", "in", "of", "and", "to", "for", "with",
            "can", "you", "explain", "describe", "tell", "me", "about", "how", "does", "do",
            "your", "experience", "working", "use", "when", "why", "would", "could", "should"
        }
        
        q_tokens = {w for w in re.findall(r'\b\w+\b', q_text) if w not in stopwords and len(w) > 2}

        for prev_q in context.questions:
            prev_text = prev_q.question.strip().lower()
            
            # 1. Exact string match
            if q_text == prev_text:
                logger.warning(f"Exact duplicate question detected: '{q_text}'")
                return True
            
            # 2. Significant keyword overlap (Jaccard similarity on non-stopwords)
            prev_tokens = {w for w in re.findall(r'\b\w+\b', prev_text) if w not in stopwords and len(w) > 2}
            if q_tokens and prev_tokens:
                intersection = q_tokens.intersection(prev_tokens)
                union = q_tokens.union(prev_tokens)
                jaccard = len(intersection) / len(union) if union else 0.0
                
                # If >65% overlap in key technical words, treat as semantic duplicate
                if jaccard >= 0.65:
                    logger.warning(f"Semantic duplicate question detected (overlap={jaccard:.2f}): '{q_text}' vs '{prev_text}'")
                    return True
                
        return False
