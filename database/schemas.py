from pydantic import BaseModel
from typing import Optional

class SessionCreate(BaseModel):
    """Schema for creating a new session record."""
    candidate_name: str

class QuestionCreate(BaseModel):
    """Schema for saving a question."""
    session_id: str
    question_text: str

class ReportCreate(BaseModel):
    """Schema for saving the final report."""
    session_id: str
    overall_score: float
