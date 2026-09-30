import re

file = 'tests/test_persistence_redis_postgres.py'
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("question_text=", "question=")

# Fix the TurnRepository.add_turn back
content = content.replace(
    'TurnRepository.add_turn(\n                session_id=session_id,\n                turn_index=1,\n                question_id="q_1",\n                question=',
    'TurnRepository.add_turn(\n                session_id=session_id,\n                turn_index=1,\n                question_id="q_1",\n                question_text='
)

# Mock LLM in the test
content = """
import pytest
import uuid
from unittest.mock import patch, AsyncMock
from shared.llm.client import LLMResponse
""" + content

content += """
@pytest.fixture(autouse=True)
def mock_llm_for_persistence():
    with patch('agents.interviewer.generator.QuestionGenerator.generate_question', new_callable=AsyncMock) as mock_q:
        from agents.shared.types import InterviewQuestion
        mock_q.return_value = InterviewQuestion(question="Mocked question?", topic="Test", estimated_difficulty="Medium")
        yield
"""

# Randomize emails
content = content.replace('"bob@example.com"', 'f"bob_{uuid.uuid4().hex[:8]}@example.com"')
content = content.replace('"charlie@example.com"', 'f"charlie_{uuid.uuid4().hex[:8]}@example.com"')
content = content.replace('"evan@example.com"', 'f"evan_{uuid.uuid4().hex[:8]}@example.com"')

with open(file, 'w', encoding='utf-8') as f:
    f.write(content)

# Also fix api/session_manager.py
sm_file = 'api/session_manager.py'
with open(sm_file, 'r', encoding='utf-8') as f:
    sm_content = f.read()
    
# Fix QuestionData instantiation
sm_content = sm_content.replace('question_text=q_text,\n            stage=q_stage', 'question=q_text,\n            stage=q_stage')

with open(sm_file, 'w', encoding='utf-8') as f:
    f.write(sm_content)

print("done")
