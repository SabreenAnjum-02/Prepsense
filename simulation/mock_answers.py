from typing import List

MOCK_ANSWERS: List[str] = [
    "I have extensive experience with Python, mostly building REST APIs.",
    "For database design, I prefer PostgreSQL and ensure normalized tables to maintain data integrity.",
    "I use Docker to containerize my applications, ensuring they run consistently across different environments.",
    "When faced with a bug, I usually write failing unit tests first, then debug the logic using logs.",
    "My proudest achievement was reducing API response times by 50% using Redis caching."
]

class MockAnswerGenerator:
    """Generates predefined answers for the simulation."""
    
    def __init__(self):
        self.index = 0

    def get_next_answer(self, question: str) -> str:
        """Returns the next predefined answer, looping if necessary."""
        answer = MOCK_ANSWERS[self.index % len(MOCK_ANSWERS)]
        self.index += 1
        return answer
