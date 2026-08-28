import asyncio
import logging
import sys

from shared.container import setup_container, container

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("VERIFY_VOICE")

async def verify():
    logger.info("Initializing dependency injection container...")
    setup_container()
    
    logger.info("Resolving VoiceService Singleton (this will pre-load ML models)...")
    # Resolve the VoiceService to trigger model loading
    voice_service = container.resolve("voice_service")
    
    # 1. Speak a sample interview question
    question = "Welcome to the interview. Could you please tell me about a time you solved a difficult technical problem?"
    logger.info(f"\n==================================================")
    logger.info(f"AI Interviewer: '{question}'")
    logger.info(f"==================================================\n")
    
    speak_success = await voice_service.speak(question)
    
    if not speak_success:
        logger.error("[FAILED] VoiceService failed to speak.")
        sys.exit(1)
        
    # 2. Automatically Listen
    logger.info("VoiceService entering hands-free listening mode.")
    logger.info("(Speak naturally into your microphone now. It will stop recording when you pause.)")
    
    result = await voice_service.listen_and_transcribe()
    
    logger.info(f"\n==================================================")
    logger.info("Voice Result Summary")
    logger.info(f"==================================================")
    
    if result.success:
        logger.info(f"Transcription   : {result.transcript}")
        logger.info(f"Confidence      : {result.confidence:.2f}")
        logger.info(f"Detected Lang   : {result.language}")
        logger.info(f"Audio Duration  : {result.audio_duration:.2f}s")
        logger.info(f"Processing Time : {result.processing_time:.2f}s (Latency)")
        logger.info(f"Session State   : {voice_service.state.value}")
        
        print("\nVoice Service verified successfully and ready for interview integration.")
    else:
        logger.error(f"[FAILED] Transcription failed: {result.error_message}")
        sys.exit(1)

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
