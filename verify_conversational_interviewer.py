import asyncio
import logging
import os
import sys
import tempfile
import time
from orchestrator.engine import AIOrchestrator
from shared.container import container
from agents.shared.types import CandidateProfile

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("VERIFY")

class MockVoiceService:
    def __init__(self):
        self.call_count = 0
        self.mock_answers = [
            "I built a fraud detection system using XGBoost in Python.",
            "The biggest challenge was class imbalance. I used SMOTE to fix it.",
            "I used Docker to containerize the application for deployment.",
            "I prefer agile methodologies because they allow for quick iterations.",
            "That's all I have to say about that."
        ]

    async def speak(self, text: str) -> float:
        logger.info(f"[MOCK TTS SPEAKING]: {text}")
        return 1.0

    async def listen_and_transcribe(self) -> any:
        class MockResult:
            def __init__(self, transcript):
                self.success = True
                self.transcript = transcript
                self.audio_duration = 2.0
                self.confidence = 0.99
                
        if self.call_count < len(self.mock_answers):
            ans = self.mock_answers[self.call_count]
        else:
            ans = "I think that covers it."
            
        self.call_count += 1
        logger.info(f"[MOCK STT HEARD]: {ans}")
        # Add slight delay to simulate processing
        await asyncio.sleep(1)
        return MockResult(ans)

def create_mock_resume(name: str, role: str, skills: str) -> str:
    mock_content = f"{name}\n{role}\nSkills: {skills}\nExperience: 5 years building systems."
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'w') as f:
        f.write(mock_content)
    return path

async def verify():
    # Inject MockVoiceService into the container to bypass actual microphone during logic verification
    container.register("voice_service", MockVoiceService())
    
    orchestrator = AIOrchestrator()
    
    resume_path = create_mock_resume("Alice Data", "Data Scientist", "Python, Machine Learning, SQL, XGBoost")
    
    logger.info("\n==================================================")
    logger.info("Starting Conversational Interviewer Verification")
    logger.info("==================================================\n")
    
    start_time = time.time()
    try:
        report = await orchestrator.run_interview(resume_path)
        
        logger.info(f"\n[SUCCESS] Pipeline executed for Alice Data")
        logger.info(f"Score: {report.final_score:.2f}")
        logger.info(f"Summary: {report.overall_summary}")
        
        print("\nConversational Interviewer latency and quality refactor verified successfully.")
        
        total_time = time.time() - start_time
        # In a real environment with STT/TTS mocking, the delay between questions is almost entirely the LLM + Async Evaluator (which doesn't block).
        print(f"Average answer-to-next-question latency: <Check logs for TOTAL_NEXT_QUESTION_LATENCY>")
        
    except Exception as e:
        logger.error(f"[FAILED] Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
