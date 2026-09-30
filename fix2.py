import re
file = 'tests/test_persistence_redis_postgres.py'
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('"alice@example.com"', 'f"alice_{uuid.uuid4().hex[:8]}@example.com"')
content = content.replace('question="How do you handle connection pooling in FastAPI?"', 'question_text="How do you handle connection pooling in FastAPI?"')
content = content.replace('q1_data.question_text', 'q1_data.question')
content = content.replace('q2_data.question_text', 'q2_data.question')

with open(file, 'w', encoding='utf-8') as f:
    f.write(content)

print("done")
