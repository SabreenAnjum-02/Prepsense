import re

file = 'api/session_manager.py'
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 1
content = content.replace("question=q_text,", "question_text=q_text,")
# Fix 2
content = content.replace("question_text=res.next_question.question_text", "question_text=res.next_question.question")

with open(file, 'w', encoding='utf-8') as f:
    f.write(content)
print("fixed")
