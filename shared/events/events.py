from dataclasses import dataclass
from typing import Any
from datetime import datetime

@dataclass
class BaseEvent:
    """Base class for all system events."""
    timestamp: datetime = datetime.now()

@dataclass
class ResumeParsed(BaseEvent):
    session_id: str
    candidate_profile: Any

@dataclass
class QuestionPlanned(BaseEvent):
    session_id: str
    plan: Any

@dataclass
class QuestionAsked(BaseEvent):
    session_id: str
    question: Any

@dataclass
class AnswerReceived(BaseEvent):
    session_id: str
    answer_text: str

@dataclass
class EvaluationCompleted(BaseEvent):
    session_id: str
    evaluation_result: Any

@dataclass
class MemoryUpdated(BaseEvent):
    session_id: str
    context: Any

@dataclass
class InterviewCompleted(BaseEvent):
    session_id: str

@dataclass
class ReportGenerated(BaseEvent):
    session_id: str
    report: Any
