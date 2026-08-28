from typing import List
from agents.shared.types import QuestionRecord, AnswerRecord
from .utils import get_logger

logger = get_logger(__name__)


class InterviewHistory:
    """Maintains the history of asked questions and their corresponding answers."""

    def __init__(self) -> None:
        self._questions: List[QuestionRecord] = []
        self._answers: List[AnswerRecord] = []

    def add_question(self, question: QuestionRecord) -> None:
        """Add a question to the history."""
        self._questions.append(question)
        logger.info(f"Added question ID: {question.question_id}")

    def add_answer(self, answer: AnswerRecord) -> None:
        """Add an answer to the history."""
        self._answers.append(answer)
        logger.info(f"Added answer for question ID: {answer.question_id}")

    def get_questions(self) -> List[QuestionRecord]:
        """Retrieve all questions asked so far."""
        return list(self._questions)

    def get_answers(self) -> List[AnswerRecord]:
        """Retrieve all answers given so far."""
        return list(self._answers)

    def clear(self) -> None:
        """Clear the history."""
        self._questions.clear()
        self._answers.clear()
