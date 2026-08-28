import logging
import io
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from agents.shared.roles import RoleArchetype, ROLE_BLUEPRINTS
from agents.planner.topic_selector import TopicSelector
from .schemas import (
    HealthResponse,
    ResumeUploadResponse,
    JDMatchRequest,
    JDMatchResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    StartInterviewResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SessionStateResponse,
    PracticalTaskResponse,
    PracticalSubmitRequest,
    PracticalSubmitResponse,
    FinalReportResponse,
    QuestionData
)
from .session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")
session_mgr = SessionManager()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Service health check and capabilities."""
    roles = [r.value for r in RoleArchetype]
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        engine="PrepSense Adaptive Assessment Engine",
        supported_roles=roles
    )


@router.post("/resume/upload", response_model=ResumeUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    target_role: Optional[str] = Form(None)
):
    """Parse candidate resume (PDF or Plain Text) and extract skills/experience."""
    try:
        content_bytes = await file.read()
        filename = file.filename or "resume.txt"
        
        raw_text = ""
        if filename.lower().endswith(".pdf"):
            try:
                import pypdf
                pdf_reader = pypdf.PdfReader(io.BytesIO(content_bytes))
                raw_text = " ".join([page.extract_text() or "" for page in pdf_reader.pages])
            except Exception as e:
                logger.warning(f"pypdf extraction failed, falling back to text decode: {e}")
                raw_text = content_bytes.decode("utf-8", errors="replace")
        else:
            raw_text = content_bytes.decode("utf-8", errors="replace")

        # Simple resilient extraction fallback
        name = "Candidate"
        email = "candidate@example.com"
        for line in raw_text.splitlines()[:5]:
            if line.strip() and len(line.strip().split()) <= 4 and "@" not in line:
                name = line.strip()
                break
        
        for word in raw_text.split():
            if "@" in word and "." in word:
                email = word.strip(",;()<>")
                break

        # Extract common tech skills
        tech_keywords = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "FastAPI",
            "PostgreSQL", "MySQL", "Redis", "Docker", "Kubernetes", "AWS", "GCP", "Terraform",
            "PyTorch", "TensorFlow", "Scikit-Learn", "REST", "gRPC", "GraphQL", "Git",
            "CI/CD", "Linux", "Tailwind", "CSS", "HTML", "Microservices", "System Design"
        ]
        found_skills = [s for s in tech_keywords if s.lower() in raw_text.lower()]
        if not found_skills:
            found_skills = ["Software Engineering", "Problem Solving", "System Architecture"]

        # Infer role archetype from skills
        detected_role = target_role or RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value
        text_lower = raw_text.lower()
        if "react" in text_lower or "frontend" in text_lower or "css" in text_lower:
            detected_role = RoleArchetype.FRONTEND_ENGINEER.value
        elif "machine learning" in text_lower or "pytorch" in text_lower or "data science" in text_lower:
            detected_role = RoleArchetype.DATA_SCIENTIST_ML.value
        elif "kubernetes" in text_lower or "devops" in text_lower or "terraform" in text_lower:
            detected_role = RoleArchetype.DEVOPS_CLOUD.value
        elif "security" in text_lower or "cybersecurity" in text_lower or "vulnerability" in text_lower:
            detected_role = RoleArchetype.CYBERSECURITY.value
        elif "figma" in text_lower or "ux" in text_lower or "ui/ux" in text_lower:
            detected_role = RoleArchetype.UI_UX_DESIGNER.value
        elif "product manager" in text_lower or "prd" in text_lower or "roadmap" in text_lower:
            detected_role = RoleArchetype.PRODUCT_MANAGER.value

        # Extract structured projects and experience mentions from resume
        projects_found = []
        experience_found = []
        for line in raw_text.splitlines():
            line_s = line.strip()
            if not line_s:
                continue
            low = line_s.lower()
            if any(term in low for term in ["project:", "application:", "platform:", "built a", "developed a", "architected", "engineered"]):
                if len(line_s) > 10 and len(projects_found) < 4:
                    projects_found.append(line_s[:100])
            elif any(term in low for term in ["years", "engineer at", "developer at", "lead at", "worked on", "responsible for"]):
                if len(line_s) > 10 and len(experience_found) < 4:
                    experience_found.append(line_s[:100])

        if not projects_found:
            projects_found = [f"{detected_role} core service application", "Production system architecture"]

        return ResumeUploadResponse(
            success=True,
            candidate_name=name,
            candidate_email=email,
            skills=found_skills,
            experience_years=3,
            detected_role=detected_role,
            raw_summary=raw_text[:300] + "..." if len(raw_text) > 300 else raw_text
        )
    except Exception as e:
        logger.error(f"Failed to process uploaded resume: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to parse resume file: {str(e)}"
        )


@router.post("/jd/match", response_model=JDMatchResponse)
async def match_job_description(request: JDMatchRequest):
    """Match Job Description with resume competencies and return role analysis."""
    jd_text = request.job_description.lower()
    
    # Detect best role archetype
    matched_role = request.target_role or RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value
    if "frontend" in jd_text or "react" in jd_text or "vue" in jd_text:
        matched_role = RoleArchetype.FRONTEND_ENGINEER.value
    elif "machine learning" in jd_text or "data scientist" in jd_text or "ml engineer" in jd_text:
        matched_role = RoleArchetype.DATA_SCIENTIST_ML.value
    elif "devops" in jd_text or "cloud platform" in jd_text or "sre" in jd_text:
        matched_role = RoleArchetype.DEVOPS_CLOUD.value
    elif "security" in jd_text or "appsec" in jd_text:
        matched_role = RoleArchetype.CYBERSECURITY.value
    elif "ui/ux" in jd_text or "product design" in jd_text:
        matched_role = RoleArchetype.UI_UX_DESIGNER.value
    elif "product manager" in jd_text or "technical product" in jd_text:
        matched_role = RoleArchetype.PRODUCT_MANAGER.value

    # Identify required competencies for this role
    blueprint = ROLE_BLUEPRINTS.get(matched_role, ROLE_BLUEPRINTS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value])
    all_competencies = blueprint.required_competencies
    
    matched = []
    missing = []
    resume_skills_lower = [s.lower() for s in request.resume_skills]
    
    for comp in all_competencies:
        comp_lower = comp.lower()
        if any(skill in comp_lower or comp_lower in skill for skill in resume_skills_lower) or comp_lower in jd_text:
            matched.append(comp)
        else:
            missing.append(comp)

    match_score = round(max(50.0, (len(matched) / max(1, len(all_competencies))) * 100.0), 1)

    return JDMatchResponse(
        matched_role=matched_role,
        match_score=match_score,
        matched_competencies=matched[:6],
        missing_competencies=missing[:4],
        role_blueprint_summary=f"Requires {len(blueprint.technical_topics)} core technical topics across {blueprint.stage_weighting}"
    )


@router.post("/assessment/create", response_model=CreateSessionResponse)
async def create_assessment(request: CreateSessionRequest):
    """Initialize a new adaptive interview assessment session."""
    session_id = await session_mgr.create_session(
        candidate_name=request.candidate_name,
        candidate_email=request.candidate_email,
        target_role=request.target_role,
        skills=request.skills,
        experience_years=request.experience_years,
        projects=request.projects,
        experience=request.experience,
        job_description=request.job_description
    )
    return CreateSessionResponse(
        session_id=session_id,
        candidate_name=request.candidate_name,
        target_role=request.target_role,
        total_stages=5,
        stage_order=["INTRODUCTION", "TECHNICAL", "PROJECTS", "BEHAVIORAL", "HR"]
    )


@router.get("/assessment/{session_id}/state", response_model=SessionStateResponse)
async def get_session_state(session_id: str):
    """Query current session status, question index, and stage for browser recovery."""
    session = await session_mgr.get_or_restore_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    context = session["context"]
    current_q = session.get("current_question")
    
    current_q_data = None
    if current_q:
        current_q_data = QuestionData(
            question_id=current_q.question_id,
            question_text=current_q.question_text,
            stage=current_q.stage.value if hasattr(current_q.stage, "value") else str(current_q.stage),
            topic=current_q.topic,
            difficulty=current_q.difficulty,
            question_index=len(context.questions),
            total_estimated=10,
            is_followup=current_q.is_followup
        )

    current_stage = "INTRODUCTION"
    if context.questions:
        current_stage = context.questions[-1].stage
    if session.get("is_interview_completed"):
        current_stage = "PRACTICAL"

    recent = [
        {"question": q.question_text, "topic": q.topic, "stage": q.stage}
        for q in context.questions[-3:]
    ]

    return SessionStateResponse(
        session_id=session_id,
        candidate_name=session["profile"].name,
        target_role=session["profile"].target_role,
        current_stage=current_stage,
        current_question_index=len(context.questions),
        questions_count=len(context.questions),
        is_practical_ready=session.get("is_interview_completed", False),
        is_completed=session.get("is_practical_completed", False),
        current_question=current_q_data,
        recent_questions=recent
    )


@router.post("/assessment/{session_id}/start", response_model=StartInterviewResponse)
async def start_interview(session_id: str):
    """Begin interview and generate Question 1."""
    try:
        q_data = await session_mgr.start_interview(session_id)
        return StartInterviewResponse(
            session_id=session_id,
            current_question=q_data,
            stage="INTRODUCTION"
        )
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    except Exception as e:
        logger.error(f"Error starting interview: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/assessment/{session_id}/respond", response_model=SubmitAnswerResponse)
async def respond_to_question(session_id: str, request: SubmitAnswerRequest):
    """Submit candidate's answer and advance the adaptive interview."""
    try:
        res = await session_mgr.submit_answer(session_id, request.answer_text)
        return res
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/assessment/{session_id}/practical", response_model=PracticalTaskResponse)
async def get_practical_task(session_id: str):
    """Retrieve designated practical assessment task for role (hidden tests omitted)."""
    try:
        session = await session_mgr.get_or_restore_session(session_id)
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
        task_data = session_mgr.get_practical_task(session_id)
        return task_data
    except HTTPException:
        raise
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")


@router.post("/assessment/{session_id}/practical/submit", response_model=PracticalSubmitResponse)
async def submit_practical_task(session_id: str, request: PracticalSubmitRequest):
    """Execute candidate submission in sandbox and return results."""
    try:
        res = await session_mgr.submit_practical(
            session_id=session_id,
            submission_code=request.submission_code,
            language=request.language
        )
        return res
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    except Exception as e:
        logger.error(f"Error evaluating practical submission: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/assessment/{session_id}/report", response_model=FinalReportResponse)
async def get_final_report(session_id: str):
    """Retrieve or generate comprehensive final 6D assessment report."""
    try:
        report = await session_mgr.generate_final_report(session_id)
        return report
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    except Exception as e:
        logger.error(f"Error generating final report: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

