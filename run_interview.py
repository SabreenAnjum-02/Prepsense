import argparse
import asyncio
import logging
import sys

# Import orchestrator
from orchestrator.engine import AIOrchestrator
from simulation.mock_resume import get_mock_resume_path

# Configure logging to keep the CLI output clean
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("CLI")

async def main():
    parser = argparse.ArgumentParser(description="Run a mock PrepSense interview end-to-end.")
    parser.add_argument("--resume", type=str, help="Path to the candidate's resume PDF.", default=None)
    args = parser.parse_args()

    resume_path = args.resume
    if not resume_path:
        logger.info("No resume provided. Generating a mock resume dynamically...")
        resume_path = get_mock_resume_path()
        
    logger.info("==================================================")
    logger.info(f"Starting PrepSense Interview Session")
    logger.info(f"Resume Path: {resume_path}")
    logger.info("==================================================\n")
    
    # Initialize Orchestrator (which uses DI container under the hood)
    orchestrator = AIOrchestrator()
    
    try:
        # Run pipeline
        report = await orchestrator.run_interview(resume_path)
        
        # Display Final Report in Terminal
        logger.info("\n==================================================")
        logger.info("INTERVIEW COMPLETED: FINAL REPORT")
        logger.info("==================================================")
        
        logger.info(f"Session ID          : {report.session_id}")
        logger.info(f"Overall Summary: {report.overall_summary}")
        logger.info(f"\nFinal Score: {report.final_score:.2f} (Confidence: {report.confidence_level})")
        logger.info(f"Hiring Recommendation: {report.hiring_recommendation}")
        logger.info(f"\nTechnical Assessment:\n{report.technical_assessment}")
        logger.info(f"\nCommunication Assessment:\n{report.communication_assessment}")
        
        logger.info("\nKey Strengths:")
        if report.strengths:
            for s in report.strengths:
                logger.info(f"  + {s}")
        else:
            logger.info("  (None recorded)")
            
        logger.info("\nAreas for Improvement:")
        if report.weaknesses:
            for w in report.weaknesses:
                logger.info(f"  - {w}")
        else:
            logger.info("  (None recorded)")

        logger.info("\nImprovement Plan:")
        if report.improvement_plan:
            for i in report.improvement_plan:
                logger.info(f"  > {i}")
        else:
            logger.info("  (None recorded)")
            
        logger.info("==================================================")

    except Exception as e:
        logger.error(f"\n[FATAL] The interview pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # Prevent Windows ProactorEventLoop from throwing RuntimeError on exit
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
