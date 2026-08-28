import logging
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    CandidateORM,
    InterviewSessionORM,
    InterviewTurnORM,
    EvaluationORM,
    PracticalEvaluationORM,
    FinalReportORM
)

logger = logging.getLogger(__name__)


class CandidateRepository:
    """Async repository for candidate profiles."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        name: str,
        email: str,
        target_role: str,
        experience_years: int = 2,
        skills: Optional[List[str]] = None,
        projects: Optional[List[str]] = None,
        experience: Optional[List[str]] = None,
        target_jd: Optional[str] = None
    ) -> CandidateORM:
        candidate = CandidateORM(
            name=name,
            email=email,
            target_role=target_role,
            experience_years=experience_years,
            skills=skills or [],
            projects=projects or [],
            experience=experience or [],
            target_jd=target_jd
        )
        self.session.add(candidate)
        await self.session.flush()
        return candidate

    async def get_by_id(self, candidate_id: str) -> Optional[CandidateORM]:
        stmt = select(CandidateORM).where(CandidateORM.id == candidate_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[CandidateORM]:
        stmt = select(CandidateORM).where(CandidateORM.email == email).order_by(CandidateORM.created_at.desc())
        res = await self.session.execute(stmt)
        return res.scalars().first()


class SessionRepository:
    """Async repository for interview sessions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        session_id: str,
        candidate_id: str,
        target_role: str,
        status: str = "CREATED",
        current_stage: str = "INTRODUCTION"
    ) -> InterviewSessionORM:
        sess = InterviewSessionORM(
            id=session_id,
            candidate_id=candidate_id,
            target_role=target_role,
            status=status,
            current_stage=current_stage,
            current_question_index=0
        )
        self.session.add(sess)
        await self.session.flush()
        return sess

    async def get_by_id(self, session_id: str, include_relations: bool = True) -> Optional[InterviewSessionORM]:
        stmt = select(InterviewSessionORM).where(InterviewSessionORM.id == session_id)
        if include_relations:
            stmt = stmt.options(
                selectinload(InterviewSessionORM.candidate),
                selectinload(InterviewSessionORM.turns),
                selectinload(InterviewSessionORM.evaluations),
                selectinload(InterviewSessionORM.practical_evaluation),
                selectinload(InterviewSessionORM.final_report)
            )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def update_state(
        self,
        session_id: str,
        status: Optional[str] = None,
        current_stage: Optional[str] = None,
        current_question_index: Optional[int] = None,
        is_interview_completed: Optional[bool] = None,
        is_practical_completed: Optional[bool] = None
    ) -> Optional[InterviewSessionORM]:
        sess = await self.get_by_id(session_id, include_relations=False)
        if not sess:
            return None

        if status is not None:
            sess.status = status
        if current_stage is not None:
            sess.current_stage = current_stage
        if current_question_index is not None:
            sess.current_question_index = current_question_index
        if is_interview_completed is not None:
            sess.is_interview_completed = is_interview_completed
        if is_practical_completed is not None:
            sess.is_practical_completed = is_practical_completed

        await self.session.flush()
        return sess


class TurnRepository:
    """Async repository for interview turns."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_turn(
        self,
        session_id: str,
        turn_index: int,
        question_id: str,
        question_text: str,
        topic: str,
        difficulty: str = "Medium",
        stage: str = "INTRODUCTION",
        is_followup: bool = False
    ) -> InterviewTurnORM:
        turn = InterviewTurnORM(
            session_id=session_id,
            turn_index=turn_index,
            question_id=question_id,
            question_text=question_text,
            topic=topic,
            difficulty=difficulty,
            stage=stage,
            is_followup=is_followup
        )
        self.session.add(turn)
        await self.session.flush()
        return turn

    async def update_answer(
        self,
        session_id: str,
        question_id: str,
        answer_text: str,
        stt_transcript: Optional[str] = None,
        time_taken_seconds: Optional[float] = None
    ) -> Optional[InterviewTurnORM]:
        stmt = (
            select(InterviewTurnORM)
            .where(
                InterviewTurnORM.session_id == session_id,
                InterviewTurnORM.question_id == question_id
            )
            .order_by(InterviewTurnORM.turn_index.desc())
        )
        res = await self.session.execute(stmt)
        turn = res.scalars().first()
        if turn:
            turn.candidate_answer = answer_text
            turn.stt_transcript = stt_transcript or answer_text
            turn.time_taken_seconds = time_taken_seconds
            await self.session.flush()
        return turn

    async def get_turns_for_session(self, session_id: str) -> List[InterviewTurnORM]:
        stmt = (
            select(InterviewTurnORM)
            .where(InterviewTurnORM.session_id == session_id)
            .order_by(InterviewTurnORM.turn_index.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())


class EvaluationRepository:
    """Async repository for question evaluations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_evaluation(
        self,
        session_id: str,
        question_id: str,
        technical_score: float,
        practical_score: float,
        problem_solving_score: float,
        communication_score: float,
        behavioral_score: float,
        role_fit_score: float,
        overall_score: float,
        confidence_score: float = 0.0,
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None,
        feedback: Optional[str] = None,
        criterion_evaluations: Optional[List[Dict[str, Any]]] = None,
        turn_id: Optional[str] = None
    ) -> EvaluationORM:
        ev = EvaluationORM(
            session_id=session_id,
            turn_id=turn_id,
            question_id=question_id,
            technical_score=technical_score,
            practical_score=practical_score,
            problem_solving_score=problem_solving_score,
            communication_score=communication_score,
            behavioral_score=behavioral_score,
            role_fit_score=role_fit_score,
            overall_score=overall_score,
            confidence_score=confidence_score,
            strengths=strengths or [],
            weaknesses=weaknesses or [],
            feedback=feedback,
            criterion_evaluations=criterion_evaluations or []
        )
        self.session.add(ev)
        await self.session.flush()
        return ev

    async def get_evaluations_for_session(self, session_id: str) -> List[EvaluationORM]:
        stmt = (
            select(EvaluationORM)
            .where(EvaluationORM.session_id == session_id)
            .order_by(EvaluationORM.created_at.asc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())


class PracticalRepository:
    """Async repository for practical assessment submissions."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_evaluation(
        self,
        session_id: str,
        task_id: str,
        task_title: str,
        role_archetype: str,
        language: str,
        tests_passed: int,
        total_tests: int,
        hidden_tests_passed: int,
        total_hidden_tests: int,
        correctness_score: float,
        edge_case_score: float,
        complexity_score: float,
        code_quality_score: float,
        overall_practical_score: float,
        time_complexity: str,
        space_complexity: str,
        feedback: Optional[str] = None,
        execution_results: Optional[List[Dict[str, Any]]] = None,
        submission_code: Optional[str] = None
    ) -> PracticalEvaluationORM:
        stmt = select(PracticalEvaluationORM).where(PracticalEvaluationORM.session_id == session_id)
        res = await self.session.execute(stmt)
        pe = res.scalar_one_or_none()

        if pe is None:
            pe = PracticalEvaluationORM(
                session_id=session_id,
                task_id=task_id,
                task_title=task_title,
                role_archetype=role_archetype,
                language=language,
                tests_passed=tests_passed,
                total_tests=total_tests,
                hidden_tests_passed=hidden_tests_passed,
                total_hidden_tests=total_hidden_tests,
                correctness_score=correctness_score,
                edge_case_score=edge_case_score,
                complexity_score=complexity_score,
                code_quality_score=code_quality_score,
                overall_practical_score=overall_practical_score,
                time_complexity=time_complexity,
                space_complexity=space_complexity,
                feedback=feedback,
                execution_results=execution_results or [],
                submission_code=submission_code
            )
            self.session.add(pe)
        else:
            pe.task_id = task_id
            pe.task_title = task_title
            pe.role_archetype = role_archetype
            pe.language = language
            pe.tests_passed = tests_passed
            pe.total_tests = total_tests
            pe.hidden_tests_passed = hidden_tests_passed
            pe.total_hidden_tests = total_hidden_tests
            pe.correctness_score = correctness_score
            pe.edge_case_score = edge_case_score
            pe.complexity_score = complexity_score
            pe.code_quality_score = code_quality_score
            pe.overall_practical_score = overall_practical_score
            pe.time_complexity = time_complexity
            pe.space_complexity = space_complexity
            pe.feedback = feedback
            pe.execution_results = execution_results or []
            pe.submission_code = submission_code

        await self.session.flush()
        return pe

    async def get_by_session_id(self, session_id: str) -> Optional[PracticalEvaluationORM]:
        stmt = select(PracticalEvaluationORM).where(PracticalEvaluationORM.session_id == session_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()


class ReportRepository:
    """Async repository for final 6D evaluation reports."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_report(
        self,
        session_id: str,
        candidate_id: str,
        overall_summary: str,
        technical_assessment: str,
        communication_assessment: str,
        hiring_recommendation: str,
        confidence_level: str,
        final_score: float,
        dimension_scores: Dict[str, float],
        strengths: Optional[List[str]] = None,
        weaknesses: Optional[List[str]] = None,
        improvement_plan: Optional[List[str]] = None
    ) -> FinalReportORM:
        stmt = select(FinalReportORM).where(FinalReportORM.session_id == session_id)
        res = await self.session.execute(stmt)
        rep = res.scalar_one_or_none()

        if rep is None:
            rep = FinalReportORM(
                session_id=session_id,
                candidate_id=candidate_id,
                overall_summary=overall_summary,
                technical_assessment=technical_assessment,
                communication_assessment=communication_assessment,
                hiring_recommendation=hiring_recommendation,
                confidence_level=confidence_level,
                final_score=final_score,
                dimension_scores=dimension_scores,
                strengths=strengths or [],
                weaknesses=weaknesses or [],
                improvement_plan=improvement_plan or []
            )
            self.session.add(rep)
        else:
            rep.overall_summary = overall_summary
            rep.technical_assessment = technical_assessment
            rep.communication_assessment = communication_assessment
            rep.hiring_recommendation = hiring_recommendation
            rep.confidence_level = confidence_level
            rep.final_score = final_score
            rep.dimension_scores = dimension_scores
            rep.strengths = strengths or []
            rep.weaknesses = weaknesses or []
            rep.improvement_plan = improvement_plan or []

        await self.session.flush()
        return rep

    async def get_by_session_id(self, session_id: str) -> Optional[FinalReportORM]:
        stmt = select(FinalReportORM).where(FinalReportORM.session_id == session_id)
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()
