import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy import (
    String,
    Text,
    Integer,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    Index
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


class CandidateORM(Base):
    """Durable candidate profile record."""
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    target_role: Mapped[str] = mapped_column(String(100), nullable=False, default="Software Engineer")
    experience_years: Mapped[int] = mapped_column(Integer, default=2)
    skills: Mapped[List[str]] = mapped_column(JSON, default=list)
    projects: Mapped[List[str]] = mapped_column(JSON, default=list)
    experience: Mapped[List[str]] = mapped_column(JSON, default=list)
    target_jd: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    sessions: Mapped[List["InterviewSessionORM"]] = relationship(
        "InterviewSessionORM", back_populates="candidate", cascade="all, delete-orphan"
    )
    reports: Mapped[List["FinalReportORM"]] = relationship(
        "FinalReportORM", back_populates="candidate", cascade="all, delete-orphan"
    )


class InterviewSessionORM(Base):
    """Durable interview session record (source of truth)."""
    __tablename__ = "interview_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_role: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="CREATED")  # CREATED, IN_PROGRESS, PRACTICAL, COMPLETED
    current_stage: Mapped[str] = mapped_column(String(50), default="INTRODUCTION")
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    is_interview_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    is_practical_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    # Relationships
    candidate: Mapped["CandidateORM"] = relationship("CandidateORM", back_populates="sessions")
    turns: Mapped[List["InterviewTurnORM"]] = relationship(
        "InterviewTurnORM", back_populates="session", cascade="all, delete-orphan", order_by="InterviewTurnORM.turn_index"
    )
    evaluations: Mapped[List["EvaluationORM"]] = relationship(
        "EvaluationORM", back_populates="session", cascade="all, delete-orphan"
    )
    practical_evaluation: Mapped[Optional["PracticalEvaluationORM"]] = relationship(
        "PracticalEvaluationORM", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )
    final_report: Mapped[Optional["FinalReportORM"]] = relationship(
        "FinalReportORM", back_populates="session", uselist=False, cascade="all, delete-orphan"
    )


class InterviewTurnORM(Base):
    """Durable record of a single question and answer turn."""
    __tablename__ = "interview_turns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_index: Mapped[int] = mapped_column(Integer, nullable=False)
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    topic: Mapped[str] = mapped_column(String(150), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), default="Medium")
    stage: Mapped[str] = mapped_column(String(50), default="INTRODUCTION")
    is_followup: Mapped[bool] = mapped_column(Boolean, default=False)
    candidate_answer: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    stt_transcript: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    time_taken_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    session: Mapped["InterviewSessionORM"] = relationship("InterviewSessionORM", back_populates="turns")
    evaluation: Mapped[Optional["EvaluationORM"]] = relationship(
        "EvaluationORM", back_populates="turn", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_turn_session_turn_index", "session_id", "turn_index"),
    )


class EvaluationORM(Base):
    """Durable evaluation result for a turn/question."""
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    turn_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("interview_turns.id", ondelete="CASCADE"), nullable=True, index=True
    )
    question_id: Mapped[str] = mapped_column(String(100), nullable=False)
    technical_score: Mapped[float] = mapped_column(Float, default=0.0)
    practical_score: Mapped[float] = mapped_column(Float, default=0.0)
    problem_solving_score: Mapped[float] = mapped_column(Float, default=0.0)
    communication_score: Mapped[float] = mapped_column(Float, default=0.0)
    behavioral_score: Mapped[float] = mapped_column(Float, default=0.0)
    role_fit_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criterion_evaluations: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    session: Mapped["InterviewSessionORM"] = relationship("InterviewSessionORM", back_populates="evaluations")
    turn: Mapped[Optional["InterviewTurnORM"]] = relationship("InterviewTurnORM", back_populates="evaluation")


class PracticalEvaluationORM(Base):
    """Durable record of candidate practical assessment execution and scoring."""
    __tablename__ = "practical_evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    task_id: Mapped[str] = mapped_column(String(100), nullable=False)
    task_title: Mapped[str] = mapped_column(String(255), nullable=False)
    role_archetype: Mapped[str] = mapped_column(String(100), nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="python")
    tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    total_tests: Mapped[int] = mapped_column(Integer, default=0)
    hidden_tests_passed: Mapped[int] = mapped_column(Integer, default=0)
    total_hidden_tests: Mapped[int] = mapped_column(Integer, default=0)
    correctness_score: Mapped[float] = mapped_column(Float, default=0.0)
    edge_case_score: Mapped[float] = mapped_column(Float, default=0.0)
    complexity_score: Mapped[float] = mapped_column(Float, default=0.0)
    code_quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    overall_practical_score: Mapped[float] = mapped_column(Float, default=0.0)
    time_complexity: Mapped[str] = mapped_column(String(50), default="N/A")
    space_complexity: Mapped[str] = mapped_column(String(50), default="N/A")
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    execution_results: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    submission_code: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    session: Mapped["InterviewSessionORM"] = relationship("InterviewSessionORM", back_populates="practical_evaluation")


class FinalReportORM(Base):
    """Durable record of candidate final 6D evaluation report."""
    __tablename__ = "final_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    candidate_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False, index=True
    )
    overall_summary: Mapped[str] = mapped_column(Text, nullable=False)
    technical_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    communication_assessment: Mapped[str] = mapped_column(Text, nullable=False)
    hiring_recommendation: Mapped[str] = mapped_column(String(50), nullable=False)
    confidence_level: Mapped[str] = mapped_column(String(50), nullable=False)
    final_score: Mapped[float] = mapped_column(Float, default=0.0)
    dimension_scores: Mapped[Dict[str, float]] = mapped_column(JSON, default=dict)
    strengths: Mapped[List[str]] = mapped_column(JSON, default=list)
    weaknesses: Mapped[List[str]] = mapped_column(JSON, default=list)
    improvement_plan: Mapped[List[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    # Relationships
    session: Mapped["InterviewSessionORM"] = relationship("InterviewSessionORM", back_populates="final_report")
    candidate: Mapped["CandidateORM"] = relationship("CandidateORM", back_populates="reports")
