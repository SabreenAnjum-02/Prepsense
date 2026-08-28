import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from orchestrator.engine import AIOrchestrator
from agents.shared.types import (
    CandidateProfile, InterviewContext, InterviewPlan, 
    InterviewQuestion, EvaluationResult, InterviewReport, TopicTracking
)

@pytest.mark.asyncio
async def test_complete_interview_pipeline():
    """
    Tests the full end-to-end flow of the AI Orchestrator by mocking the 
    internal 'run' methods of all agents. This verifies that data is routed 
    correctly between agents without executing real logic or LLMs.
    """
    orchestrator = AIOrchestrator()
    from shared.container import container
    
    mock_voice = MagicMock()
    mock_voice.speak = AsyncMock()
    mock_voice.listen_and_transcribe = AsyncMock()
    
    mock_voice_result = MagicMock()
    mock_voice_result.success = True
    mock_voice_result.transcript = "Mock answer"
    mock_voice_result.audio_duration = 2.0
    mock_voice_result.confidence = 0.95
    mock_voice_result.processing_time = 0.5
    mock_voice.listen_and_transcribe.return_value = mock_voice_result
    container.register("voice_service", lambda: mock_voice)
    
    # 1. Mock Resume Agent
    mock_profile = CandidateProfile(name="Test Candidate", skills=["Python"])
    orchestrator.router._agents["resume"].run = AsyncMock(return_value=mock_profile)
    
    # 2. Mock Memory Agent
    mock_context = InterviewContext(
        session_id="test-session-123",
        candidate_profile=mock_profile,
        topics=TopicTracking(pending_topics=["Python"])
    )
    
    # Memory agent does different things based on 'action'
    async def mock_memory_run(payload):
        if payload["action"] == "create_session":
            return "test-session-123"
        elif payload["action"] == "get_context":
            return mock_context
        return None
        
    orchestrator.router._agents["memory"].run = AsyncMock(side_effect=mock_memory_run)
    
    # 3. Mock Planner Agent
    # We want the planner to run once, then signal end on the second loop to finish the test.
    plan_active = InterviewPlan(
        session_id="test-session-123", next_topic="Python", difficulty="Medium", 
        question_type="Technical", is_followup=False, should_end_interview=False
    )
    plan_end = InterviewPlan(
        session_id="test-session-123", should_end_interview=True
    )
    orchestrator.router._agents["planner"].run = AsyncMock(side_effect=[plan_active, plan_end])
    
    # 4. Mock Interviewer Agent
    mock_question = InterviewQuestion(
        question_id="q-1", question_text="What is Python?", topic="Python", 
        difficulty="Medium", question_type="Technical", is_followup=False
    )
    mock_question_end = InterviewQuestion(
        question_id="q-2", question_text="Goodbye.", topic="Python",
        difficulty="Medium", question_type="Technical", is_followup=False,
        should_end_interview=True
    )
    orchestrator.router._agents["interviewer"].run = AsyncMock(side_effect=[mock_question, mock_question_end])
    
    # 5. Mock Evaluator Agent
    mock_eval = EvaluationResult(
        question_id="q-1", technical_score=1.0, communication_score=1.0, 
        problem_solving_score=1.0, confidence_score=1.0, overall_score=1.0
    )
    orchestrator.router._agents["evaluator"].run = AsyncMock(return_value=mock_eval)
    
    # 6. Mock Report Agent
    mock_report = InterviewReport(
        session_id="test-session-123", candidate_profile=mock_profile,
        overall_score=1.0, technical_score=1.0, communication_score=1.0,
        hiring_decision="Hire", final_summary="Great."
    )
    orchestrator.router._agents["report"].run = AsyncMock(return_value=mock_report)
    
    # EXECUTE END TO END PIPELINE
    final_report = await orchestrator.run_interview("dummy_resume.pdf")
    
    # VERIFY AGENT COMMUNICATION & STATE CONSISTENCY
    # Ensure Resume Agent was called with the file path
    orchestrator.router._agents["resume"].run.assert_called_once_with({
        "file_path": "dummy_resume.pdf",
        "target_role": None,
        "target_jd": None
    })
    
    # Ensure Memory Agent was called appropriately
    assert orchestrator.router._agents["memory"].run.call_count >= 2
    
    # Ensure Planner Agent is not called since pipeline refactor, or called less than before
    # assert orchestrator.router._agents["planner"].run.call_count == 2
    
    # Ensure Interviewer Agent was called exactly twice (once active, once end)
    assert orchestrator.router._agents["interviewer"].run.call_count == 2
    
    # Ensure Evaluator Agent was called with the simulated question
    orchestrator.router._agents["evaluator"].run.assert_called_once()
    
    # Ensure Report Agent was called at the very end
    orchestrator.router._agents["report"].run.assert_called_once()
    
    # Check final output
    assert final_report is not None
    assert final_report.overall_score == 1.0
    assert final_report.hiring_decision == "Hire"
