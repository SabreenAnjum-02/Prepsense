import asyncio
import os
import sys
import tempfile
from agents.resume.agent import ResumeAgent

SAMPLE_RESUME_1 = """
JOHN DOE
johndoe@email.com | (555) 123-4567 | github.com/johndoe

TARGET ROLE
Senior Software Engineer

PROFESSIONAL SUMMARY
Experienced backend engineer with 5 years of experience building scalable microservices in Python and Go.

SKILLS
- Languages: Python, Go, JavaScript, SQL
- Frameworks: FastAPI, Django, React
- Tools: Docker, Kubernetes, Git
- Databases: PostgreSQL, Redis, MongoDB

EXPERIENCE
Software Engineer | TechCorp Inc. | Jan 2020 - Present
- Designed and implemented RESTful APIs using FastAPI.
- Optimized database queries, reducing latency by 40%.

EDUCATION
B.S. in Computer Science | University of Technology | 2015 - 2019

PROJECTS
- AuthSystem: A centralized JWT authentication service. (github.com/johndoe/auth)
"""

SAMPLE_RESUME_2 = """
JANE SMITH
jane.smith@email.com
LinkedIn: linkedin.com/in/janesmith

Summary
Data Scientist specializing in machine learning and predictive analytics.

Experience
Data Scientist, DataGen
June 2021 - Present
- Built predictive models using XGBoost and Scikit-Learn.
- Deployed ML pipelines in AWS using SageMaker.

Skills
Python, R, SQL, TensorFlow, PyTorch, Pandas, AWS, Docker

Education
M.S. in Data Science, State University, 2021
"""

async def run_verification():
    # Setup loop policy on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
    print("Initializing ResumeAgent (now LLM powered)...")
    agent = ResumeAgent()
    
    samples = [("John Doe", SAMPLE_RESUME_1), ("Jane Smith", SAMPLE_RESUME_2)]
    
    for name, content in samples:
        print(f"\n======================================")
        print(f"Processing Resume for: {name}")
        print(f"======================================")
        
        # Write to temp text file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tf:
            tf.write(content)
            temp_path = tf.name
            
        try:
            profile = await agent.run({"file_path": temp_path})
            if profile:
                print("\n[SUCCESS] CandidateProfile generated via LLM:")
                print(profile.model_dump_json(indent=2))
            else:
                print("\n[FAILED] ResumeAgent returned None.")
        except Exception as e:
            print(f"\n[ERROR] Exception during processing: {e}")
        finally:
            os.remove(temp_path)

if __name__ == "__main__":
    asyncio.run(run_verification())
