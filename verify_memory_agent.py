import asyncio
import sys
import uuid
from datetime import datetime
from agents.memory.agent import MemoryAgent
from agents.shared.types import CandidateProfile, QuestionRecord, AnswerRecord, PerformanceRecord

async def run_verification():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("Initializing MemoryAgent...")
    agent = MemoryAgent()
    session_id = str(uuid.uuid4())
    
    print(f"\n1. Starting new interview session: {session_id}")
    await agent.run({
        "session_id": session_id,
        "action": "initialize_session",
        "payload": None
    })
    
    print("\n2. Loading CandidateProfile into memory...")
    profile = CandidateProfile(
        name="Test Candidate",
        email="test@example.com",
        skills=["Python", "FastAPI"],
        experience=["Backend Engineer"]
    )
    
    await agent.run({
        "session_id": session_id,
        "action": "store_candidate_profile",
        "payload": profile
    })
    
    print("\n3. Simulating interview questions, answers, and evaluations...")
    # Question 1
    q1_id = str(uuid.uuid4())
    q1 = QuestionRecord(
        question_id=q1_id,
        question="What is a REST API?",
        topic="Web Development",
        difficulty="Medium"
    )
    await agent.run({"session_id": session_id, "action": "add_question", "payload": q1})
    
    a1 = AnswerRecord(
        question_id=q1_id,
        candidate_answer="A REST API uses HTTP methods like GET and POST.",
        stt_transcript="A REST API uses HTTP methods like GET and POST.",
        time_taken_seconds=45,
        confidence=0.85
    )
    await agent.run({"session_id": session_id, "action": "add_answer", "payload": a1})
    
    p1 = PerformanceRecord(
        question_id=q1_id,
        technical_score=0.8,
        communication_score=0.9,
        confidence_score=0.85,
        emotion_score=0.7,
        overall_score=0.8
    )
    await agent.run({"session_id": session_id, "action": "update_scores", "payload": p1})

    # Question 2
    q2_id = str(uuid.uuid4())
    q2 = QuestionRecord(
        question_id=q2_id,
        question="Explain dependency injection.",
        topic="Software Design",
        difficulty="Hard"
    )
    await agent.run({"session_id": session_id, "action": "add_question", "payload": q2})
    
    a2 = AnswerRecord(
        question_id=q2_id,
        candidate_answer="I am not fully sure, but it involves passing dependencies.",
        stt_transcript="I am not fully sure, but it involves passing dependencies.",
        time_taken_seconds=15,
        confidence=0.4
    )
    await agent.run({"session_id": session_id, "action": "add_answer", "payload": a2})
    
    p2 = PerformanceRecord(
        question_id=q2_id,
        technical_score=0.4,
        communication_score=0.5,
        confidence_score=0.4,
        emotion_score=0.5,
        overall_score=0.45
    )
    await agent.run({"session_id": session_id, "action": "update_scores", "payload": p2})
    
    print("\n4. Retrieving final interview memory context...")
    context = await agent.run({
        "session_id": session_id,
        "action": "get_context"
    })
    
    print("\n================ FINAL MEMORY CONTEXT ================\n")
    print(context.model_dump_json(indent=2))
    
    print("\n================ VERIFICATION SUMMARY ================")
    assert context.session_id == session_id, "Session ID mismatch!"
    assert context.candidate_profile.name == "Test Candidate", "Candidate profile lost!"
    assert len(context.questions) == 2, "Questions lost!"
    assert len(context.answers) == 2, "Answers lost!"
    assert len(context.performance) == 2, "Performance lost!"
    assert "Web Development" in context.topics.strong_topics, "Topic tracking failed for strengths!"
    assert "Software Design" in context.topics.weak_topics, "Topic tracking failed for weaknesses!"
    assert context.statistics.total_questions == 2, "Stats mismatch!"
    assert context.statistics.interview_duration_seconds == 60, "Duration calculation failed!"
    
    print("\nMemory Agent verified successfully and ready for Planner Agent integration.")

if __name__ == "__main__":
    asyncio.run(run_verification())
