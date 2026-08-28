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
logger = logging.getLogger("VERIFY_INTERVIEWER")

async def verify():
    logger.info("\n==================================================")
    logger.info("Initializing Interviewer Latency Profiling")
    logger.info("==================================================\n")

    # 1. Initialize DI Container (so RAG is available if configured)
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
    
    # Mock some realistic previous answers
    mock_answers = [
        "I built the fraud detection system using XGBoost. The main challenge was class imbalance.",
        "To solve the imbalance, I applied SMOTE and tuned the class weights in XGBoost.",
        "For deployment, I packaged the model in a Docker container and deployed it on Kubernetes to handle spikes."
    ]

    for i in range(3):
        logger.info(f"\n--- Running Interviewer Question {i+1} ---")
        
        t_start = time.perf_counter()
        
        # 5. Run Interviewer
        question = await interviewer.run({"context": context})
        
        t_total = time.perf_counter() - t_start
        
        if not question:
            logger.error("Interviewer returned None!")
            break
            
        logger.info(f"Generated Question: {question.question}")
        
        # Append question and fake answer to context so the next iteration has history
        context.questions.append(question)
        
        # Provide the mock answer to simulate conversation progressing
        context.answers.append(
            AnswerRecord(
                question_id=question.question_id,
                candidate_answer=mock_answers[i],
                stt_transcript=mock_answers[i],
                time_taken_seconds=15,
                confidence=0.95
            )
        )
        
        # Wait a moment before the next request
        await asyncio.sleep(1)

    logger.info("\nInterviewer LLM latency profiling completed successfully.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
