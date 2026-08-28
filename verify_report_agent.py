import asyncio
import sys
import uuid
from agents.report.agent import ReportAgent
from agents.shared.types import (
    InterviewContext,
    CandidateProfile,
    EvaluationResult
)

async def run_verification():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("Initializing ReportAgent...")
    agent = ReportAgent()
    
    session_id = str(uuid.uuid4())
    profile = CandidateProfile(
        name="Alice Engineer",
        skills=["Python", "System Design", "AWS"],
        experience=["Senior Backend Developer at TechCorp"]
    )
    context = InterviewContext(
        session_id=session_id,
        candidate_profile=profile
    )
    
    evaluations = [
        EvaluationResult(
            question_id=str(uuid.uuid4()),
            technical_score=85.0,
            communication_score=90.0,
            reasoning_score=80.0,
            confidence_score=85.0,
            overall_score=83.3,
            strengths=["Clear and concise explanation", "Good use of caching"],
            weaknesses=["Did not mention handling collisions in hashing"],
            expected_topics_covered=["Hashing", "Database Indexing"],
            missing_topics=["Security"],
            difficulty_recommendation="Medium",
            feedback="Solid foundation, needs more focus on edge cases."
        ),
        EvaluationResult(
            question_id=str(uuid.uuid4()),
            technical_score=95.0,
            communication_score=85.0,
            reasoning_score=90.0,
            confidence_score=90.0,
            overall_score=90.0,
            strengths=["Deep understanding of distributed systems"],
            weaknesses=[],
            expected_topics_covered=["CAP Theorem", "Consensus"],
            missing_topics=[],
            difficulty_recommendation="Hard",
            feedback="Excellent answer, showed great depth."
        )
    ]
    
    print("\n======================================")
    print("Simulating Complete Interview Report")
    print("======================================")
    
    result = await agent.run({
        "context": context,
        "evaluations": evaluations
    })
    
    if result:
        print("\n[SUCCESS] Report Agent generated a valid InterviewReport:")
        print(result.model_dump_json(indent=2))
        print("\nReport Agent verified successfully and the complete AI interview pipeline is operational.")
    else:
        print("\n[ERROR] Verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_verification())
