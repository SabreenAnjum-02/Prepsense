import asyncio
import sys
import uuid
from agents.interviewer.agent import InterviewerAgent
from agents.shared.types import (
    InterviewContext,
    CandidateProfile,
    InterviewPlan,
    QuestionRecord
)

async def simulate_scenario(agent: InterviewerAgent, scenario_name: str, context: InterviewContext, plan: InterviewPlan):
    print(f"\n======================================")
    print(f"Simulating Scenario: {scenario_name}")
    print(f"======================================")
    
    question = await agent.run({"context": context, "plan": plan})
    
    if question:
        print("\n[SUCCESS] Interviewer generated a valid InterviewQuestion:")
        print(question.model_dump_json(indent=2))
        return True
    else:
        print("\n[ERROR] Interviewer failed to generate a valid question.")
        return False

async def run_verification():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("Initializing InterviewerAgent...")
    agent = InterviewerAgent()
    
    # Scenario 1: Initial Question
    profile1 = CandidateProfile(
        name="Alice Engineer",
        skills=["Python", "System Design", "AWS"],
        experience=["Senior Backend Developer at TechCorp"]
    )
    context1 = InterviewContext(
        session_id=str(uuid.uuid4()),
        candidate_profile=profile1
    )
    plan1 = InterviewPlan(
        session_id=context1.session_id,
        next_topic="System Design",
        difficulty="Medium",
        objective="Assess basic understanding of system design principles",
        question_type="Technical",
        is_followup=False,
        priority="High"
    )
    
    success1 = await simulate_scenario(agent, "Initial System Design Question", context1, plan1)
    
    # Scenario 2: Follow-up Question
    context2 = InterviewContext(
        session_id=str(uuid.uuid4()),
        candidate_profile=profile1,
        questions=[
            QuestionRecord(
                question_id=str(uuid.uuid4()),
                question="How would you design a URL shortener system?",
                topic="System Design",
                difficulty="Medium"
            )
        ]
    )
    plan2 = InterviewPlan(
        session_id=context2.session_id,
        next_topic="System Design",
        difficulty="Hard",
        objective="Assess deep understanding of scaling databases and caching",
        question_type="Technical",
        is_followup=True,
        priority="High"
    )
    
    success2 = await simulate_scenario(agent, "Follow-up System Design Question", context2, plan2)
    
    if success1 and success2:
        print("\nInterviewer Agent verified successfully and ready for Evaluator Agent integration.")
    else:
        print("\n[ERROR] Verification failed.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_verification())
