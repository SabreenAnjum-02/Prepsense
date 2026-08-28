from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "2.0.0"
    engine: str = "PrepSense Adaptive Assessment Engine"
    supported_roles: List[str] = Field(default_factory=list)


class ResumeUploadResponse(BaseModel):
    success: bool
    candidate_name: str
    candidate_email: str
    skills: List[str] = Field(default_factory=list)
    experience_years: int = 1
    detected_role: Optional[str] = None
    raw_summary: str = ""


class JDMatchRequest(BaseModel):
    job_description: str
    resume_skills: List[str] = Field(default_factory=list)
    target_role: Optional[str] = None


class JDMatchResponse(BaseModel):
    matched_role: str
    match_score: float
    matched_competencies: List[str] = Field(default_factory=list)
    missing_competencies: List[str] = Field(default_factory=list)
    role_blueprint_summary: str = ""


class CreateSessionRequest(BaseModel):
    candidate_name: str
    candidate_email: str
    target_role: str
    skills: List[str] = Field(default_factory=list)
    experience_years: int = 2
    projects: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    job_description: Optional[str] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    total_stages: int = 5
    stage_order: List[str] = Field(default_factory=list)


class QuestionData(BaseModel):
    question_id: str
    question_text: str
    stage: str
    topic: str
    difficulty: str
    question_index: int
    total_estimated: int = 10
    is_followup: bool = False


class StartInterviewResponse(BaseModel):
    session_id: str
    current_question: QuestionData
    stage: str


class SubmitAnswerRequest(BaseModel):
    answer_text: str
    audio_duration_seconds: Optional[float] = None


class SubmitAnswerResponse(BaseModel):
    session_id: str
    answer_acknowledged: bool = True
    next_question: Optional[QuestionData] = None
    current_stage: str
    is_practical_ready: bool = False
    is_completed: bool = False
    total_questions_asked: int = 0


class SessionStateResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    current_stage: str
    current_question_index: int
    questions_count: int
    is_practical_ready: bool = False
    is_completed: bool = False
    current_question: Optional[QuestionData] = None
    recent_questions: List[Dict[str, Any]] = Field(default_factory=list)


class VisibleTestCase(BaseModel):
    test_case_id: str
    input_params: Any
    expected_output: Any
    description: str = ""


class PracticalTaskResponse(BaseModel):
    task_id: str
    title: str
    description: str
    role_archetype: str
    task_type: str
    language: str
    starter_code: str = ""
    instructions: str = ""
    visible_test_cases: List[VisibleTestCase] = Field(default_factory=list)
    hidden_test_count: int = 0
    time_limit_minutes: int = 15


class PracticalSubmitRequest(BaseModel):
    submission_code: str
    language: Optional[str] = None


class ExecutionResultItem(BaseModel):
    test_case_id: str
    passed: bool
    actual_output: Optional[Any] = None
    expected_output: Optional[Any] = None
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None


class PracticalSubmitResponse(BaseModel):
    task_id: str
    task_title: str
    role_archetype: str
    language: str
    tests_passed: int
    total_tests: int
    hidden_tests_passed: int
    total_hidden_tests: int
    correctness_score: float
    edge_case_score: float
    complexity_score: float
    code_quality_score: float
    overall_practical_score: float
    time_complexity: str = "N/A"
    space_complexity: str = "N/A"
    feedback: str = ""
    execution_results: List[ExecutionResultItem] = Field(default_factory=list)


class DimensionScores(BaseModel):
    technical: float = 0.0
    practical: float = 0.0
    problem_solving: float = 0.0
    communication: float = 0.0
    behavioral: float = 0.0
    role_fit: float = 0.0
    confidence: float = 0.0
    overall: float = 0.0


class FinalReportResponse(BaseModel):
    session_id: str
    candidate_name: str
    target_role: str
    overall_summary: str
    technical_assessment: str
    communication_assessment: str
    hiring_recommendation: str
    confidence_level: str
    final_score: float
    dimension_scores: DimensionScores
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_plan: List[str] = Field(default_factory=list)
    practical_evaluation: Optional[Dict[str, Any]] = None

