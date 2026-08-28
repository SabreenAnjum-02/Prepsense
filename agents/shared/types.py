from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from datetime import datetime
import uuid

class CandidateProfile(BaseModel):
    name: str = Field(..., description="Candidate's full name")
    email: Optional[str] = Field(None, description="Candidate's email address")
    phone: Optional[str] = Field(None, description="Candidate's phone number")
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL")
    github: Optional[str] = Field(None, description="GitHub profile URL")
    skills: List[str] = Field(default_factory=list, description="List of skills")
    education: List[str] = Field(default_factory=list, description="Education details")
    experience: List[str] = Field(default_factory=list, description="Work experience details")
    projects: List[str] = Field(default_factory=list, description="Projects")
    certifications: List[str] = Field(default_factory=list, description="Certifications")
    achievements: List[str] = Field(default_factory=list, description="Achievements")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    target_role: Optional[str] = Field(None, description="Target job role archetype")
    target_jd: Optional[str] = Field(None, description="Target Job Description text")
    skill_matches: List[str] = Field(default_factory=list, description="Matched skills with JD")
    skill_gaps: List[str] = Field(default_factory=list, description="Missing skills from JD")
    jd_match_percentage: float = Field(default=0.0, description="Match score percentage against JD")


class QuestionRecord(BaseModel):
    question_id: str
    question: str
    topic: str
    difficulty: str
    is_followup: bool = False
    timestamp: datetime = Field(default_factory=datetime.now)

class AnswerRecord(BaseModel):
    question_id: str
    candidate_answer: str
    stt_transcript: str
    time_taken_seconds: int
    confidence: float
    timestamp: datetime = Field(default_factory=datetime.now)

class PerformanceRecord(BaseModel):
    question_id: str
    technical_score: float = 0.0
    practical_score: float = 0.0
    problem_solving_score: float = 0.0
    communication_score: float = 0.0
    behavioral_score: float = 0.0
    role_fit_score: float = 0.0
    confidence_score: float = 0.0
    emotion_score: float = 0.0
    overall_score: float = 0.0

class TopicTracking(BaseModel):
    covered_topics: List[str] = Field(default_factory=list)
    pending_topics: List[str] = Field(default_factory=list)
    weak_topics: List[str] = Field(default_factory=list)
    strong_topics: List[str] = Field(default_factory=list)

class InterviewStatistics(BaseModel):
    total_questions: int = 0
    average_technical_score: float = 0.0
    average_communication_score: float = 0.0
    average_confidence_score: float = 0.0
    interview_duration_seconds: int = 0

class InterviewCoverage(BaseModel):
    categories_covered: List[str] = Field(default_factory=list)
    categories_remaining: List[str] = Field(default_factory=list)
    questions_per_category: Dict[str, int] = Field(default_factory=dict)
    current_topic_follow_up_count: int = 0
    overall_progress: float = 0.0

class InterviewContext(BaseModel):
    session_id: str
    candidate_profile: Optional[CandidateProfile] = None
    questions: List[QuestionRecord] = Field(default_factory=list)
    answers: List[AnswerRecord] = Field(default_factory=list)
    performance: List[PerformanceRecord] = Field(default_factory=list)
    topics: TopicTracking = Field(default_factory=TopicTracking)
    statistics: InterviewStatistics = Field(default_factory=InterviewStatistics)
    coverage: InterviewCoverage = Field(default_factory=InterviewCoverage)
    practical_evaluation: Optional['PracticalEvaluation'] = None

class InterviewStage(str, Enum):
    INTRODUCTION = "INTRODUCTION"
    RESUME = "RESUME"
    TECHNICAL = "TECHNICAL"
    PROJECTS = "PROJECTS"
    CODING = "CODING"
    BEHAVIORAL = "BEHAVIORAL"
    PSYCHOLOGICAL = "PSYCHOLOGICAL"
    GENERAL_KNOWLEDGE = "GENERAL_KNOWLEDGE"
    HR = "HR"
    CLOSING = "CLOSING"

class InterviewPlan(BaseModel):
    session_id: str
    next_topic: Optional[str] = None
    difficulty: str = "Medium"
    objective: str = "Assess core competency"
    question_type: str = "Technical"
    is_followup: bool = False
    interview_stage: InterviewStage = InterviewStage.INTRODUCTION
    reason: str = ""
    should_end_interview: bool = False

class InterviewQuestion(BaseModel):
    question_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversational_filler: str = ""
    question: str = ""
    topic: str = ""
    estimated_difficulty: str = ""
    question_type: str = ""
    is_followup: bool = False
    follow_up_questions: List[str] = Field(default_factory=list)
    expected_topics: List[str] = Field(default_factory=list)
    should_end_interview: bool = False

    @model_validator(mode='before')
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = dict(data)
            if 'question_text' in new_data and 'question' not in new_data:
                new_data['question'] = new_data.pop('question_text')
            if 'difficulty' in new_data and 'estimated_difficulty' not in new_data:
                new_data['estimated_difficulty'] = new_data.pop('difficulty')
            return new_data
        return data

class CriterionEvaluation(BaseModel):
    criterion_name: str = "Technical Criterion"
    expected_evidence: List[str] = Field(default_factory=list)
    observed_evidence: List[str] = Field(default_factory=list)
    missing_evidence: List[str] = Field(default_factory=list)
    incorrect_evidence: List[str] = Field(default_factory=list)
    score: float = Field(default=0.0, description="Raw criterion score (0.0 to 100.0)")
    max_score: float = Field(default=100.0)
    confidence: str = Field(default="MEDIUM", description="HIGH, MEDIUM, or LOW")
    reasoning: str = ""

    @model_validator(mode='before')
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                clean_k = str(k).replace(',', '_').replace(' ', '_').lower()
                if clean_k in ['criterion_name', 'criterionname', 'criterion', 'name']:
                    new_data['criterion_name'] = str(v)
                elif clean_k in ['expected_evidence', 'expectedevidence', 'expected']:
                    new_data['expected_evidence'] = v if isinstance(v, list) else [str(v)]
                elif clean_k in ['observed_evidence', 'observedevidence', 'observed']:
                    new_data['observed_evidence'] = v if isinstance(v, list) else [str(v)]
                elif clean_k in ['missing_evidence', 'missingevidence', 'missing']:
                    new_data['missing_evidence'] = v if isinstance(v, list) else [str(v)]
                elif clean_k in ['incorrect_evidence', 'incorrectevidence', 'incorrect', 'false_evidence']:
                    new_data['incorrect_evidence'] = v if isinstance(v, list) else [str(v)]
                elif clean_k in ['score', 'criterion_score']:
                    try:
                        new_data['score'] = float(v)
                    except (ValueError, TypeError):
                        new_data['score'] = 0.0
                elif clean_k in ['confidence']:
                    new_data['confidence'] = str(v).upper()
                elif clean_k in ['reasoning', 'explanation']:
                    new_data['reasoning'] = str(v)
                else:
                    new_data[k] = v
            if 'criterion_name' not in new_data:
                new_data['criterion_name'] = "General Technical Criterion"
            return new_data
        return data

class EvaluationResult(BaseModel):
    question_id: str = ""
    technical_score: float = 0.0
    practical_score: float = 0.0
    problem_solving_score: float = 0.0
    communication_score: float = 0.0
    behavioral_score: float = 0.0
    role_fit_score: float = 0.0
    reasoning_score: float = 0.0
    confidence_score: float = 0.0
    overall_score: float = 0.0
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    expected_topics_covered: List[str] = Field(default_factory=list)
    missing_topics: List[str] = Field(default_factory=list)
    difficulty_recommendation: str = "Medium"
    feedback: str = ""
    criterion_evaluations: List[CriterionEvaluation] = Field(default_factory=list)

class TaskType(str, Enum):
    CODING = "CODING"
    SYSTEM_DESIGN_CASE = "SYSTEM_DESIGN_CASE"
    PRD_CASE = "PRD_CASE"
    UX_DESIGN_CASE = "UX_DESIGN_CASE"
    INFRA_SCRIPT = "INFRA_SCRIPT"
    DATA_ANALYSIS = "DATA_ANALYSIS"


class TestCase(BaseModel):
    test_case_id: str
    input_params: Any
    expected_output: Any
    is_hidden: bool = False
    description: str = ""
    timeout_seconds: float = 3.0


class ExecutionResult(BaseModel):
    test_case_id: str
    passed: bool
    actual_output: Any = None
    expected_output: Any = None
    stdout: str = ""
    stderr: str = ""
    execution_time_ms: float = 0.0
    error_message: Optional[str] = None
    timeout_occurred: bool = False


class PracticalTask(BaseModel):
    task_id: str
    title: str
    description: str
    role_archetype: str
    task_type: TaskType = TaskType.CODING
    language: str = "python"  # "python", "javascript", "markdown"
    starter_code: str = ""
    function_name: Optional[str] = None
    visible_test_cases: List[TestCase] = Field(default_factory=list)
    hidden_test_cases: List[TestCase] = Field(default_factory=list)
    time_limit_minutes: int = 15
    instructions: str = ""
    rubric: Optional[Dict[str, str]] = None


class PracticalEvaluation(BaseModel):
    task_id: str
    task_title: str
    role_archetype: str
    language: str
    tests_passed: int = 0
    total_tests: int = 0
    hidden_tests_passed: int = 0
    total_hidden_tests: int = 0
    correctness_score: float = 0.0
    edge_case_score: float = 0.0
    complexity_score: float = 0.0
    code_quality_score: float = 0.0
    overall_practical_score: float = 0.0
    time_complexity: str = "N/A"
    space_complexity: str = "N/A"
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    feedback: str = ""
    execution_results: List[ExecutionResult] = Field(default_factory=list)


class InterviewReport(BaseModel):
    session_id: str = ""
    overall_summary: str = ""
    technical_assessment: str = ""
    communication_assessment: str = ""
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    improvement_plan: List[str] = Field(default_factory=list)
    hiring_recommendation: str = ""
    confidence_level: str = "Medium"
    final_score: float = 0.0
    practical_evaluation: Optional[PracticalEvaluation] = None

    @property
    def hiring_decision(self) -> str:
        return self.hiring_recommendation

    @property
    def final_summary(self) -> str:
        return self.overall_summary

    @property
    def overall_score(self) -> float:
        return self.final_score

    @model_validator(mode='before')
    @classmethod
    def _normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            new_data = dict(data)
            if 'hiring_decision' in new_data:
                new_data['hiring_recommendation'] = new_data.pop('hiring_decision')
            if 'final_summary' in new_data:
                new_data['overall_summary'] = new_data.pop('final_summary')
            if 'overall_score' in new_data:
                new_data['final_score'] = new_data.pop('overall_score')
            # ignore unused older fields
            for f in ['candidate_profile', 'technical_score', 'communication_score', 'topic_performance', 'recommendations']:
                new_data.pop(f, None)
            return new_data
        return data


class VoiceAnalysisResult(BaseModel):
    speaking_speed: float
    pause_count: int
    fluency_score: float
    consistency_score: float
    confidence_score: float
    duration_seconds: float


class EmotionAnalysisResult(BaseModel):
    primary_emotion: str
    emotion_scores: Dict[str, float] = Field(default_factory=dict)
    engagement_score: float
    confidence_level: float
    face_detected: bool


# Resolve forward references
InterviewContext.model_rebuild()


