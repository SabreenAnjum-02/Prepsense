import asyncio
import logging
import os
import sys
import tempfile
from orchestrator.engine import AIOrchestrator

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("VERIFY")

def create_mock_resume(name: str, role: str, skills: str) -> str:
    mock_content = f"{name}\n{role}\nSkills: {skills}\nExperience: 5 years building systems."
    fd, path = tempfile.mkstemp(suffix=".pdf")
    with os.fdopen(fd, 'w') as f:
        f.write(mock_content)
    return path

async def verify():
    roles = [
        {"name": "Alice Developer", "role": "Software Engineer", "skills": "Python, React, AWS"},
        {"name": "Bob Data", "role": "Data Scientist", "skills": "Python, Machine Learning, SQL"},
        {"name": "Charlie Manager", "role": "Product Manager", "skills": "Agile, Strategy, Communication"}
    ]
    
    orchestrator = AIOrchestrator()
    
    for r in roles:
        resume_path = create_mock_resume(r["name"], r["role"], r["skills"])
        logger.info(f"\n==================================================")
        logger.info(f"Verifying Role: {r['role']} (Candidate: {r['name']})")
        logger.info(f"==================================================")
        try:
            report = await orchestrator.run_interview(resume_path)
            
            logger.info(f"\n[SUCCESS] Pipeline executed for {r['name']}")
            logger.info(f"Score: {report.final_score:.2f}")
            logger.info(f"Recommendation: {report.hiring_recommendation}")
            logger.info(f"Confidence: {report.confidence_level}")
            logger.info(f"Summary: {report.overall_summary}")
        except Exception as e:
            logger.error(f"[FAILED] Pipeline failed for {r['name']}: {e}")
            sys.exit(1)
            
    print("\nPrepSense AI Engine verified successfully. Ready for Voice Pipeline integration.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify())
