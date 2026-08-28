from .mock_answers import MockAnswerGenerator
import logging

logger = logging.getLogger(__name__)

class MockCandidate:
    """Represents a simulated candidate participating in the interview."""
    
    def __init__(self):
        self.answer_generator = MockAnswerGenerator()

    def provide_answer(self, question: str) -> str:
        """Simulates the candidate thinking and returning a predefined answer."""
        logger.info(f"MockCandidate: Formulating answer for question: '{question}'")
        return self.answer_generator.get_next_answer(question)
