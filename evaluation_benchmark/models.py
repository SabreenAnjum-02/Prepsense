from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ExpectedScores(BaseModel):
    technical_score: float = Field(..., description="Expected technical score (0.0 to 100.0)")
    communication_score: float = Field(..., description="Expected communication score (0.0 to 100.0)")
    reasoning_score: float = Field(..., description="Expected reasoning score (0.0 to 100.0)")
    confidence_score: float = Field(..., description="Expected confidence score (0.0 to 100.0)")
    overall_score: float = Field(..., description="Expected overall score (0.0 to 100.0)")


class BenchmarkAnswer(BaseModel):
    quality_level: str = Field(..., description="Quality tier: excellent, good, average, weak, incorrect")
    candidate_answer: str = Field(..., description="The candidate's text answer")
    expected_scores: ExpectedScores = Field(..., description="Ground-truth expected scores")


class BenchmarkCase(BaseModel):
    case_id: str = Field(..., description="Unique case identifier")
    question: str = Field(..., description="Interview question text")
    topic: str = Field(..., description="Topic area (e.g. Python, SQL, System Design)")
    estimated_difficulty: str = Field(..., description="Difficulty level (Easy, Medium, Hard)")
    expected_topics: List[str] = Field(default_factory=list, description="Key concepts expected in answer")
    evaluation_rubric: str = Field(..., description="Rubric defining scoring expectations for quality levels")
    answers: List[BenchmarkAnswer] = Field(..., description="Answer variants for testing")


class EvaluationPrediction(BaseModel):
    case_id: str
    topic: str
    quality_level: str
    question: str
    candidate_answer: str
    expected_score: float
    predicted_score: float
    absolute_error: float
    error_delta: float  # predicted - expected
    is_pass_pm1: bool    # absolute_error <= 1.0 (out of 100)
    is_pass_pm2: bool    # absolute_error <= 2.0 (out of 100)
    is_pass_pm10: bool   # absolute_error <= 10.0 (out of 100, equivalent to +-1 on 10-pt scale)
    is_pass_pm20: bool   # absolute_error <= 20.0 (out of 100, equivalent to +-2 on 10-pt scale)
    predicted_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class BenchmarkSummary(BaseModel):
    total_cases: int
    total_evaluations: int
    passed_evaluations: int
    failed_evaluations: int
    mae: float
    accuracy_pm1: float
    accuracy_pm2: float
    accuracy_pm10: float
    accuracy_pm20: float
    expected_average_score: float
    predicted_average_score: float
    largest_errors: List[EvaluationPrediction] = Field(default_factory=list)
    identified_weaknesses: List[str] = Field(default_factory=list)
