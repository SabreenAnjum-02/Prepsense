import pytest
from unittest.mock import MagicMock
from agents.evaluator.agent import EvaluatorAgent
from agents.shared.types import InterviewQuestion, EvaluationResult, InterviewContext, CandidateProfile

@pytest.fixture
def mock_scoring():
    scoring = MagicMock()
    scoring.calculate_scores.return_value = (0.8, 0.7, 0.9, 0.85, 0.8)
    return scoring

@pytest.fixture
def mock_feedback():
    feedback = MagicMock()
    feedback.generate_feedback.return_value = (["Good clarity"], ["More depth needed"], ["Read up on X"])
    return feedback

@pytest.fixture
def mock_metrics():
    metrics = MagicMock()
    metrics.compile.return_value = EvaluationResult(
        question_id="q-123",
        technical_score=0.8,
        communication_score=0.7,
        problem_solving_score=0.9,
        confidence_score=0.85,
        overall_score=0.8,
        strengths=["Good clarity"],
        weaknesses=["More depth needed"],
        improvement_suggestions=["Read up on X"]
    )
    return metrics

@pytest.fixture
def mock_validator():
    validator = MagicMock()
    validator.validate_input.return_value = True
    validator.validate_output.return_value = True
    return validator

@pytest.mark.asyncio
async def test_evaluator_agent_success(mock_scoring, mock_feedback, mock_metrics, mock_validator):
    agent = EvaluatorAgent(scoring=mock_scoring, feedback=mock_feedback, metrics=mock_metrics)
    agent._validator = mock_validator

    q = InterviewQuestion(question_id="q-123", question_text="What is Python?", topic="Python", difficulty="Easy", question_type="Technical", is_followup=False)
    input_data = {
        "question": q,
        "answer": "Python is a language.",
        "context": InterviewContext(session_id="session-123"),
        "profile": CandidateProfile(name="John Doe")
    }
    
    result = await agent.run(input_data)

    assert result is not None
    assert isinstance(result, EvaluationResult)
    assert result.question_id == "q-123"
    assert result.overall_score == 0.8
    assert "Good clarity" in result.strengths

@pytest.mark.asyncio
async def test_evaluator_agent_missing_keys(mock_validator):
    agent = EvaluatorAgent()
    agent._validator = mock_validator

    with pytest.raises(ValueError, match="EvaluatorAgent input missing one of"):
        await agent.run({"question": "Missing answer and context"})
