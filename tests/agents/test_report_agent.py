import pytest
from unittest.mock import MagicMock
from agents.report.agent import ReportAgent
from agents.shared.types import InterviewContext, EvaluationResult, InterviewReport, CandidateProfile

@pytest.fixture
def mock_builder():
    builder = MagicMock()
    builder.build.return_value = InterviewReport(
        session_id="session-123",
        candidate_profile=CandidateProfile(name="John Doe"),
        overall_score=0.85,
        technical_score=0.9,
        communication_score=0.8,
        topic_performance={"Python": 0.9},
        strengths=["Good coding"],
        weaknesses=[],
        recommendations=["Hire him"],
        hiring_decision="Strong Hire",
        final_summary="Great performance."
    )
    return builder

@pytest.fixture
def mock_validator():
    validator = MagicMock()
    validator.validate_inputs.return_value = True
    validator.validate_output.return_value = True
    return validator

@pytest.mark.asyncio
async def test_report_agent_success(mock_builder, mock_validator):
    agent = ReportAgent(builder=mock_builder)
    agent._validator = mock_validator

    context = InterviewContext(session_id="session-123")
    evals = [EvaluationResult(
        question_id="q-1", technical_score=0.9, communication_score=0.8,
        problem_solving_score=0.9, confidence_score=0.9, overall_score=0.85
    )]
    
    input_data = {"context": context, "evaluations": evals}
    
    result = await agent.run(input_data)

    assert result is not None
    assert isinstance(result, InterviewReport)
    assert result.session_id == "session-123"
    assert result.hiring_decision == "Strong Hire"
    mock_builder.build.assert_called_once_with(context, evals)

@pytest.mark.asyncio
async def test_report_agent_invalid_input(mock_validator):
    mock_validator.validate_inputs.return_value = False
    agent = ReportAgent()
    agent._validator = mock_validator

    with pytest.raises(ValueError, match="Invalid inputs provided"):
        await agent.run({"context": InterviewContext(session_id="s1"), "evaluations": []})
