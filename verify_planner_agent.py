import asyncio
import sys
import uuid
from agents.planner.agent import PlannerAgent
from agents.shared.types import (
    InterviewContext,
    CandidateProfile,
    QuestionRecord,
    AnswerRecord,
    PerformanceRecord,
    TopicTracking,
    InterviewStatistics
)

async def simulate_scenario(agent: PlannerAgent, scenario_name: str, context: InterviewContext):
    print(f"\n======================================")
    print(f"Simulating Scenario: {scenario_name}")
    print(f"======================================")
    
    plan = await agent.run({"context": context})
    
    if plan:
        print("\n[SUCCESS] Planner generated a valid InterviewPlan:")
        print(plan.model_dump_json(indent=2))
        return True
    else:
        print("\n[ERROR] Planner failed to generate a valid plan.")
        return False

async def run_verification():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("Initializing PlannerAgent...")
    agent = PlannerAgent()
    
    # Scenario 1: New Interview (No history)
    profile1 = CandidateProfile(
        name="Alice Engineer",
        skills=["Python", "System Design", "AWS"],
        experience=["Senior Backend Developer at TechCorp"]
    )
    context1 = InterviewContext(
        session_id=str(uuid.uuid4()),
        candidate_profile=profile1
    )
    
    success1 = await simulate_scenario(agent, "New Interview (No History)", context1)
    
    # Scenario 2: Mid-Interview (Good Performance)
    q_id = str(uuid.uuid4())
    context2 = InterviewContext(
        session_id=str(uuid.uuid4()),
        candidate_profile=profile1,
        questions=[
            QuestionRecord(
                question_id=q_id,
                question="How would you design a scalable URL shortener?",
                topic="System Design",
                difficulty="Medium"
            )
        ],
        answers=[
            AnswerRecord(
                question_id=q_id,
                candidate_answer="I would use a key-value store, a hashing algorithm like Base62, and put a load balancer in front of API servers.",
                stt_transcript="...",
                time_taken_seconds=120,
                confidence=0.9
            )
        ],
        performance=[
            PerformanceRecord(
                question_id=q_id,
                technical_score=0.9,
                communication_score=0.85,
                confidence_score=0.9,
                emotion_score=0.8,
                overall_score=0.9
            )
        ],
        topics=TopicTracking(
            covered_topics=["System Design"],
            strong_topics=["System Design"]
        ),
        statistics=InterviewStatistics(
            total_questions=1,
            average_technical_score=0.9,
            average_communication_score=0.85,
            average_confidence_score=0.9,
            interview_duration_seconds=120
        )
    )
    
    success2 = await simulate_scenario(agent, "Mid-Interview (Good Performance)", context2)
    
    # Scenario 3: Nearing End (Poor Performance on specific topic)
    q2_id = str(uuid.uuid4())
    context3 = InterviewContext(
        session_id=str(uuid.uuid4()),
        candidate_profile=CandidateProfile(
            name="Bob Junior",
            skills=["JavaScript", "React"],
            experience=["Junior Frontend Developer"]
        ),
        questions=[
            QuestionRecord(
                question_id=q2_id,
                question="Explain the event loop in Node.js",
                topic="Node.js",
                difficulty="Medium"
            )
        ],
        answers=[
            AnswerRecord(
                question_id=q2_id,
                candidate_answer="I don't know much about the backend.",
                stt_transcript="I don't know much about the backend.",
                time_taken_seconds=10,
                confidence=0.2
            )
        ],
        performance=[
            PerformanceRecord(
                question_id=q2_id,
                technical_score=0.2,
                communication_score=0.5,
                confidence_score=0.2,
                emotion_score=0.4,
                overall_score=0.3
            )
        ],
        topics=TopicTracking(
            covered_topics=["Node.js"],
            weak_topics=["Node.js"]
        ),
        statistics=InterviewStatistics(
            total_questions=4, # Pre-existing
            average_technical_score=0.4,
            average_communication_score=0.5,
            average_confidence_score=0.3,
            interview_duration_seconds=600
        )
    )
    
    success3 = await simulate_scenario(agent, "Mid-Interview (Poor Performance on Topic)", context3)
    
    if success1 and success2 and success3:
        print("\nPlanner Agent verified successfully and ready for Interviewer Agent integration.")
    else:
        print("\n[ERROR] Verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_verification())
