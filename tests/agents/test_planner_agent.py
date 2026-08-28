import pytest
from unittest.mock import MagicMock
from agents.planner.agent import PlannerAgent
from agents.shared.types import InterviewContext, InterviewPlan

@pytest.fixture
def mock_difficulty():
    diff = MagicMock()
    diff.adjust_difficulty.return_value = "Hard"
    return diff

@pytest.fixture
def mock_strategy():
    strat = MagicMock()
    strat.determine_strategy.return_value = {"should_change_topic": False, "should_end_interview": False}
    return strat

@pytest.fixture
def mock_topic_selector():
    selector = MagicMock()
    selector.select_next_topic.return_value = "System Design"
    return selector

@pytest.fixture
def mock_followup():
    followup = MagicMock()
    followup.should_ask_followup.return_value = False
    return followup

@pytest.fixture
def mock_decision_engine():
    engine = MagicMock()
    engine.decide_next_step.return_value = InterviewPlan(
        session_id="session-123",
        next_topic="System Design",
        difficulty="Hard",
        question_type="Technical",
        is_followup=False
    )
    return engine

@pytest.fixture
def mock_validator():
    validator = MagicMock()
    validator.validate_input.return_value = True
    validator.validate_output.return_value = True
    return validator

@pytest.mark.asyncio
async def test_planner_agent_success(mock_decision_engine, mock_validator):
    agent = PlannerAgent(decision_engine=mock_decision_engine)
    agent._validator = mock_validator

    context = InterviewContext(session_id="session-123")
    input_data = {"context": context}
    
    result = await agent.run(input_data)

    assert result is not None
    assert isinstance(result, InterviewPlan)
    assert result.session_id == "session-123"
    assert result.next_topic == "System Design"
    assert result.difficulty == "Hard"
    
    mock_decision_engine.decide_next_step.assert_called_once_with(context)

@pytest.mark.asyncio
async def test_planner_agent_invalid_input(mock_validator):
    mock_validator.validate_input.return_value = False
    agent = PlannerAgent()
    agent._validator = mock_validator

    with pytest.raises(ValueError, match="Invalid input"):
        await agent.run({"context": None})
