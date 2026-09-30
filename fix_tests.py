import os
import re

files_to_fix = [
    "tests/test_persistence_redis_postgres.py",
    "tests/test_phase4_api.py",
    "tests/test_phase5_voice.py",
    "tests/agents/test_evaluator_agent.py",
    "tests/integration/test_end_to_end_flow.py",
    "tests/test_conversational_grounding.py",
]

for file in files_to_fix:
    if not os.path.exists(file):
        continue
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace question_text with question
    content = re.sub(r'question_text\s*=', 'question=', content)
    content = content.replace("q1['question_text']", "q1['question']")
    content = content.replace("q1_data.question_text", "q1_data.question")
    content = content.replace("next_question.question_text", "next_question.question")
    
    # Replace difficulty with estimated_difficulty in InterviewQuestion calls
    # This requires a bit of care, we'll do a simple replace since difficulty= is mostly used there
    content = re.sub(r'(InterviewQuestion\([^)]*)difficulty\s*=', r'\1estimated_difficulty=', content)
    
    with open(file, 'w', encoding='utf-8') as f:
        f.write(content)
print('Fixed test fields')
