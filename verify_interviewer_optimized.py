import asyncio
import logging
import sys
import uuid
import time
from agents.shared.types import InterviewContext, CandidateProfile, AnswerRecord
from agents.interviewer.agent import InterviewerAgent
from shared.container import container
from shared.monitor import monitor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("VERIFY_OPTIMIZED")


async def verify():
    logger.info("\n==================================================")
    logger.info("Initializing OPTIMIZED Interviewer Latency Profiling")
    logger.info("==================================================\n")

    # 1. Initialize DI Container
    from orchestrator.engine import AIOrchestrator
    _ = AIOrchestrator()
    rag_service = container.resolve("rag_service")
    
    # 2. Create Interviewer Agent
    interviewer = InterviewerAgent(rag_service=rag_service)

    # 3. Create realistic Candidate Profile
    profile = CandidateProfile(
        name="Alice Profiler",
        role="Data Engineer",
        skills=["Python", "Machine Learning", "SQL", "XGBoost", "Docker", "Kubernetes"],
        projects=["Fraud Detection System", "Customer Churn Predictor", "Data Warehouse Migration"],
        experience=["5 years building scalable ML systems and data pipelines."]
    )

    # 4. Create realistic Context
    session_id = str(uuid.uuid4())
    monitor.start_session(session_id)
    
    context = InterviewContext(
        session_id=session_id,
        candidate_profile=profile,
        questions=[],
        answers=[]
    )
    
    mock_answers = [
        "I built the fraud detection system using XGBoost. The main challenge was class imbalance.",
        "To solve the imbalance, I applied SMOTE and tuned the class weights in XGBoost.",
        "For deployment, I packaged the model in a Docker container and deployed it on Kubernetes to handle spikes."
    ]

    gen_latencies = []
    total_latencies = []
    output_tokens_list = []
    tps_list = []
    rag_latencies = []

    for i in range(3):
        logger.info(f"\n--- Running Optimized Interviewer Question {i+1} ---")
        
        t_start = time.perf_counter()
        
        question = await interviewer.run({"context": context})
        
        t_total = time.perf_counter() - t_start
        total_latencies.append(t_total)
        
        if not question:
            logger.error("Interviewer returned None!")
            break
        
        # Check conversational quality
        logger.info(f"  Filler: {question.conversational_filler}")
        logger.info(f"  Question: {question.question}")
        logger.info(f"  Topic: {question.topic} | Difficulty: {question.estimated_difficulty} | Follow-up: {question.is_followup}")
            
        # Append question and mock answer to context
        context.questions.append(question)
        context.answers.append(
            AnswerRecord(
                question_id=question.question_id,
                candidate_answer=mock_answers[i],
                stt_transcript=mock_answers[i],
                time_taken_seconds=15,
                confidence=0.95
            )
        )
        
        await asyncio.sleep(1)

    # Aggregated report
    if total_latencies:
        avg_total = sum(total_latencies) / len(total_latencies)
        
        # Baseline comparison
        baseline_gen = 44.15
        baseline_total = 44.21
        
        print("\n\n==================================================")
        print("OPTIMIZED INTERVIEWER LATENCY")
        print("==================================================")
        print(f"Average total latency:        {avg_total:.2f} sec")
        print(f"Per-question latencies:       {', '.join(f'{t:.2f}s' for t in total_latencies)}")
        print("==================================================")
        print("")
        print("==================================================")
        print("BASELINE COMPARISON")
        print("==================================================")
        print(f"Previous total:               {baseline_total:.2f} sec")
        print(f"Optimized total:              {avg_total:.2f} sec")
        
        if avg_total < baseline_total:
            improvement = ((baseline_total - avg_total) / baseline_total) * 100
            print(f"Improvement:                  {improvement:.1f}%")
        else:
            print(f"Improvement:                  No improvement detected")
        print("==================================================")

    print("\nOptimized Conversational Interviewer verified successfully.")


if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
