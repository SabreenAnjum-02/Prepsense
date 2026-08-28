import asyncio
import sys
import uuid
from datetime import datetime
from agents.evaluator.agent import EvaluatorAgent
from agents.shared.types import (
    InterviewContext,
    CandidateProfile,
    InterviewQuestion,
    AnswerRecord
)

async def simulate_scenario(agent: EvaluatorAgent, scenario_name: str, question: InterviewQuestion, answer: AnswerRecord, context: InterviewContext, profile: CandidateProfile):
    print(f"\n======================================")
    print(f"Simulating Scenario: {scenario_name}")
    print(f"======================================")
    
    result = await agent.run({
        "question": question,
        "answer": answer,
        "context": context,
        "profile": profile
    })
    
    if result:
        print("\n[SUCCESS] Evaluator generated a valid EvaluationResult:")
        print(result.model_dump_json(indent=2))
        return True
    else:
        print("\n[ERROR] Evaluator failed to generate a valid EvaluationResult.")
        return False

async def run_verification():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("Initializing EvaluatorAgent...")
    agent = EvaluatorAgent()
    
    profile = CandidateProfile(
        name="Alice Engineer",
        skills=["Python", "System Design", "AWS"],
        experience=["Senior Backend Developer at TechCorp"]
    )
    context = InterviewContext(
        session_id=str(uuid.uuid4()),
        candidate_profile=profile
    )
    
    # Scenario 1: Strong Answer
    q1 = InterviewQuestion(
        question_id=str(uuid.uuid4()),
        question="How would you design a scalable URL shortener like Bitly?",
        topic="System Design",
        estimated_difficulty="Medium",
        question_type="Technical",
        is_followup=False,
        expected_topics=["Hashing", "Database Indexing", "Load Balancing"]
    )
    a1 = AnswerRecord(
        question_id=q1.question_id,
        candidate_answer="I would use a highly available NoSQL database like DynamoDB to store the short to long URL mappings. I would generate the short URL using base62 encoding of an auto-incrementing ID or a distributed ID generator like Snowflake. To handle high read traffic, I would place a caching layer like Redis in front of the database. The API servers would be behind a load balancer to distribute incoming requests.",
        stt_transcript="",
        time_taken_seconds=45,
        confidence=0.9
    )
    
    success1 = await simulate_scenario(agent, "Strong System Design Answer", q1, a1, context, profile)
    
    # Scenario 2: Weak Answer
    q2 = InterviewQuestion(
        question_id=str(uuid.uuid4()),
        question="What is the difference between a process and a thread?",
        topic="Operating Systems",
        estimated_difficulty="Easy",
        question_type="Technical",
        is_followup=False,
        expected_topics=["Memory Space", "Context Switching", "Concurrency"]
    )
    a2 = AnswerRecord(
        question_id=q2.question_id,
        candidate_answer="Uh, a process is like a program running, and a thread is... something inside it. I think processes share memory but threads don't. Or maybe it's the other way around. I'm not entirely sure about the details.",
        stt_transcript="",
        time_taken_seconds=60,
        confidence=0.3
    )
    
    success2 = await simulate_scenario(agent, "Weak OS Answer", q2, a2, context, profile)
    
    if success1 and success2:
        print("\nEvaluator Agent verified successfully and ready for Report Agent integration.")
    else:
        print("\n[ERROR] Verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_verification())
