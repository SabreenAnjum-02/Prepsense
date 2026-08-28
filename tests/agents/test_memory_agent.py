import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.memory.agent import MemoryAgent
from agents.shared.types import InterviewContext, CandidateProfile

@pytest.fixture
def mock_session_memory():
    sm = MagicMock()
    sm.create_session.return_value = "session-123"
    sm.get_session.return_value = InterviewContext(session_id="session-123")
    return sm

@pytest.fixture
def mock_candidate_memory():
    cm = MagicMock()
    cm.update_profile.return_value = None
    return cm

@pytest.fixture
def mock_history():
    hist = MagicMock()
    hist.add_question.return_value = None
    hist.add_answer.return_value = None
    return hist

@pytest.fixture
def mock_validator():
    validator = MagicMock()
    validator.validate_action.return_value = True
    return validator

@pytest.mark.asyncio
async def test_memory_agent_create_session(mock_session_memory, mock_validator):
    agent = MemoryAgent(session_memory=mock_session_memory)
    agent._validator = mock_validator

    input_data = {"action": "create_session"}
    result = await agent.run(input_data)

    assert result == "session-123"
    mock_session_memory.create_session.assert_called_once()

@pytest.mark.asyncio
async def test_memory_agent_get_context(mock_session_memory, mock_validator):
    agent = MemoryAgent(session_memory=mock_session_memory)
    agent._validator = mock_validator

    input_data = {"action": "get_context", "session_id": "session-123"}
    result = await agent.run(input_data)

    assert isinstance(result, InterviewContext)
    assert result.session_id == "session-123"
    mock_session_memory.get_session.assert_called_once_with("session-123")

@pytest.mark.asyncio
async def test_memory_agent_invalid_action(mock_validator):
    agent = MemoryAgent()
    agent._validator = mock_validator

    with pytest.raises(ValueError, match="Unknown action"):
        await agent.run({"action": "unknown_action"})
