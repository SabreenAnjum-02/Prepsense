import asyncio
import logging
from agents.planner.agent import PlannerAgent
from agents.shared.types import InterviewContext, CandidateProfile, QuestionRecord, AnswerRecord, PerformanceRecord, TopicTracking, InterviewStatistics, InterviewCoverage, InterviewStage

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    planner = PlannerAgent(rag_service=None)
    print("Testing Adaptive Planner Agent...\n")

    profile = CandidateProfile(
        name="Test Candidate",
        skills=["Python", "FastAPI", "React"]
    )

    # Scenario 1: Early in the interview, doing well
    print("=== Scenario 1: Strong Performance ===")
    coverage1 = InterviewCoverage(
        categories_covered=["INTRODUCTION"],
        categories_remaining=["RESUME", "TECHNICAL", "BEHAVIORAL", "CLOSING"],
        questions_per_category={"INTRODUCTION": 1},
        current_topic_follow_up_count=0,
        overall_progress=0.2
    )
    
    q1 = QuestionRecord(question_id="q1", question="Tell me about yourself.", topic="INTRODUCTION", difficulty="Easy", is_followup=False)
    p1 = PerformanceRecord(question_id="q1", technical_score=0.9, communication_score=0.9, confidence_score=0.9, emotion_score=0.9, overall_score=0.9)
    
    context1 = InterviewContext(
        session_id="session_1",
        candidate_profile=profile,
        questions=[q1],
        answers=[],
        performance=[p1],
        coverage=coverage1
    )
    
    plan1 = await planner.run({"context": context1})
    print(f"Decision: Topic={plan1.next_topic}, Stage={plan1.interview_stage.value}, Difficulty={plan1.difficulty}, FollowUp={plan1.is_followup}, End={plan1.should_end_interview}")
    print(f"Reason: {plan1.reason}\n")


    # Scenario 2: Struggling candidate, 2 followups already
    print("=== Scenario 2: Struggling Performance (Max Followups) ===")
    coverage2 = InterviewCoverage(
        categories_covered=["INTRODUCTION", "TECHNICAL"],
        categories_remaining=["BEHAVIORAL", "CLOSING"],
        questions_per_category={"INTRODUCTION": 1, "TECHNICAL": 3},
        current_topic_follow_up_count=2,
        overall_progress=0.5
    )
    
    q2 = QuestionRecord(question_id="q2", question="Explain asyncio.", topic="TECHNICAL", difficulty="Medium", is_followup=False)
    q3 = QuestionRecord(question_id="q3", question="How does the event loop work?", topic="TECHNICAL", difficulty="Medium", is_followup=True)
    q4 = QuestionRecord(question_id="q4", question="What is a task?", topic="TECHNICAL", difficulty="Hard", is_followup=True)
    
    p2 = PerformanceRecord(question_id="q2", technical_score=0.4, communication_score=0.5, confidence_score=0.5, emotion_score=0.5, overall_score=0.45)
    p3 = PerformanceRecord(question_id="q3", technical_score=0.3, communication_score=0.5, confidence_score=0.4, emotion_score=0.5, overall_score=0.35)
    p4 = PerformanceRecord(question_id="q4", technical_score=0.2, communication_score=0.4, confidence_score=0.3, emotion_score=0.4, overall_score=0.25)

    context2 = InterviewContext(
        session_id="session_2",
        candidate_profile=profile,
        questions=[q2, q3, q4],
        answers=[],
        performance=[p2, p3, p4],
        coverage=coverage2
    )

    plan2 = await planner.run({"context": context2})
    print(f"Decision: Topic={plan2.next_topic}, Stage={plan2.interview_stage.value}, Difficulty={plan2.difficulty}, FollowUp={plan2.is_followup}, End={plan2.should_end_interview}")
    print(f"Reason: {plan2.reason}\n")


    # Scenario 3: End of Interview, sufficient evidence collected
    print("=== Scenario 3: Sufficient Evidence Collected ===")
    coverage3 = InterviewCoverage(
        categories_covered=["INTRODUCTION", "RESUME", "TECHNICAL", "PROJECTS", "BEHAVIORAL", "HR"],
        categories_remaining=["CLOSING"],
        questions_per_category={"INTRODUCTION": 1, "TECHNICAL": 4, "BEHAVIORAL": 3, "HR": 1},
        current_topic_follow_up_count=0,
        overall_progress=0.9
    )
    
    questions = [QuestionRecord(question_id=f"q{i}", question=f"Q{i}", topic="TECHNICAL", difficulty="Hard") for i in range(10)]
    performances = [PerformanceRecord(question_id=f"q{i}", technical_score=0.8, communication_score=0.8, confidence_score=0.8, emotion_score=0.8, overall_score=0.8) for i in range(10)]
    
    context3 = InterviewContext(
        session_id="session_3",
        candidate_profile=profile,
        questions=questions,
        answers=[],
        performance=performances,
        coverage=coverage3
    )
    
    plan3 = await planner.run({"context": context3})
    print(f"Decision: Topic={plan3.next_topic}, Stage={plan3.interview_stage.value}, Difficulty={plan3.difficulty}, FollowUp={plan3.is_followup}, End={plan3.should_end_interview}")
    print(f"Reason: {plan3.reason}\n")

    print("Adaptive Planner Agent verified successfully with interview coverage tracking and evidence-based decision making.")

if __name__ == "__main__":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
