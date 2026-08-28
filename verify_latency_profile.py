import asyncio
import logging
import os
import sys
import tempfile
import time
from orchestrator.engine import AIOrchestrator
from shared.container import container
from shared.monitor import monitor

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("VERIFY")

class MockTTS:
    def __init__(self):
        self.last_synthesis_latency = -1.0

class MockVoiceService:
    """Mocks VoiceService entirely to avoid kokoro ImportError on this system."""
    def __init__(self):
        self.call_count = 0
        self.mock_answers = [
            "I built a fraud detection system using XGBoost in Python. It was very effective.",
            "The biggest challenge was class imbalance. I used SMOTE to fix it and it improved recall.",
            "I used Docker to containerize the application for deployment and orchestrated it with Kubernetes."
        ]
        self.tts = MockTTS()

    async def speak(self, text: str) -> bool:
        logger.info(f"[MOCK TTS SPEAKING]: {text}")
        await asyncio.sleep(0.5)
        return True

    async def listen_and_transcribe(self) -> any:
        class MockResult:
            def __init__(self, transcript):
                self.success = True
                self.transcript = transcript
                self.audio_duration = 3.0
                self.confidence = 0.99
                self.processing_time = -1.0 # unavailable due to mock
                self.error_message = ""
                
        if self.call_count < len(self.mock_answers):
            ans = self.mock_answers[self.call_count]
        else:
            ans = "I think that covers it."
            
        self.call_count += 1
        logger.info(f"[MOCK STT HEARD]: {ans}")
        
        # Simulate slight delay representing user speaking
        await asyncio.sleep(self.call_count * 0.5)
        return MockResult(ans)

def create_mock_resume(name: str, role: str, skills: str) -> str:
    mock_content = f"{name}\n{role}\nSkills: {skills}\nExperience: 5 years building systems."
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'w') as f:
        f.write(mock_content)
    return path

async def verify():
    # 1. Initialize Real Pipeline
    import os
    os.environ["PREPSENSE_MAX_QUESTIONS"] = "3"
    orchestrator = AIOrchestrator()
    
    # Wrap the real VoiceService to mock microphone
    mock_voice = MockVoiceService()
    container.register("voice_service", lambda: mock_voice, singleton=True)
    
    resume_path = create_mock_resume("Alice Latency", "Data Engineer", "Python, Machine Learning, SQL, XGBoost")
    
    logger.info("\n==================================================")
    logger.info("Starting Latency Profiling Verification")
    logger.info("==================================================\n")
    
    try:
        report = await orchestrator.run_interview(resume_path)
        
        # Give a small delay to ensure all background evaluators finished logging
        await asyncio.sleep(2)
        
        # Fetch stats from monitor
        stats = None
        for session_id, metrics in monitor._sessions.items():
            stats = monitor.end_session(session_id)
            break
            
        if not stats:
            logger.error("No session stats found!")
            sys.exit(1)
            
        latencies = stats.get("agent_average_latencies_seconds", {})
        
        print("\n\n==================================================")
        print("LATENCY PROFILING REPORT")
        print("==================================================")
        
        def format_val(key):
            val = latencies.get(key, -1.0)
            if val < 0:
                return "Unavailable (Mocked)"
            return f"{val:.2f} sec"
            
        print(f"{'Component':<35} {'Average':<20}")
        print("-" * 55)
        print(f"{'STT_LATENCY':<35} {format_val('STT_LATENCY'):<20}")
        print(f"{'RAG_LATENCY':<35} {format_val('RAG_LATENCY'):<20}")
        print(f"{'INTERVIEWER_LATENCY':<35} {format_val('INTERVIEWER_LATENCY'):<20}")
        print(f"{'EVALUATOR_LATENCY':<35} {format_val('EVALUATOR_LATENCY'):<20}")
        print(f"{'MEMORY_LATENCY':<35} {format_val('MEMORY_LATENCY'):<20}")
        print(f"{'TTS_LATENCY':<35} {format_val('TTS_LATENCY'):<20}")
        print("-" * 55)
        print(f"{'TOTAL_NEXT_QUESTION_LATENCY':<35} {format_val('TOTAL_NEXT_QUESTION_LATENCY'):<20}")
        print("==================================================")
        
        # Calculate max bottleneck
        # We exclude TOTAL and mock metrics
        available_metrics = {k: v for k, v in latencies.items() if v > 0 and k not in ["TOTAL_NEXT_QUESTION_LATENCY", "TTS_LATENCY", "STT_LATENCY"]}
        if available_metrics:
            bottleneck = max(available_metrics, key=available_metrics.get)
            print(f"\nPrimary latency bottleneck: {bottleneck}")
        
        print(f"Average answer-to-next-question latency: {format_val('TOTAL_NEXT_QUESTION_LATENCY')}")
        print("\nPrepSense latency profiling completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
