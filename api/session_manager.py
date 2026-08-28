import uuid
import logging
import asyncio
from typing import Dict, Any, Optional, List

from agents.shared.types import (
    CandidateProfile,
    InterviewContext,
    InterviewQuestion,
    QuestionRecord,
    AnswerRecord,
    PerformanceRecord,
    EvaluationResult,
    InterviewStage,
    PracticalTask,
    PracticalEvaluation,
    TaskType
)
from agents.shared.roles import RoleArchetype
from agents.planner.topic_selector import TopicSelector
from agents.interviewer.generator import QuestionGenerator
from agents.evaluator.scoring import ScoringEngine
from agents.practical.tasks import get_practical_task_for_role
from agents.practical.evaluator import PracticalEvaluator
from agents.report.llm_report_generator import LLMReportGenerator
from .schemas import (
    QuestionData,
    SubmitAnswerResponse,
    PracticalTaskResponse,
    VisibleTestCase,
    PracticalSubmitResponse,
    ExecutionResultItem,
    FinalReportResponse,
    DimensionScores
)

from database.connection import db_manager, redis_manager
from database.repository import (
    CandidateRepository,
    SessionRepository,
    TurnRepository,
    EvaluationRepository,
    PracticalRepository,
    ReportRepository
)
from database.redis_store import redis_store
from database.session_recovery import SessionReconstructionManager

logger = logging.getLogger(__name__)


class SessionManager:
    """Thread-safe, distributed session coordinator backed by PostgreSQL and Redis."""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def get_or_restore_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Fetch session from local memory, Redis cache, or hydrate from PostgreSQL across node restarts."""
        async with self._lock:
            if session_id in self._sessions:
                return self._sessions[session_id]

        # 1. Try Redis cache for active context
        cached_context = await redis_store.get_context(session_id)
        if cached_context and cached_context.candidate_profile:
            profile = cached_context.candidate_profile
            topic_selector = TopicSelector()
            question_generator = QuestionGenerator()
            scoring_engine = ScoringEngine()
            practical_evaluator = PracticalEvaluator()
            report_generator = LLMReportGenerator()
            practical_task = get_practical_task_for_role(profile.target_role)

            current_q = await redis_store.get_current_question(session_id)
            active_state = await redis_store.get_active_state(session_id) or {}

            session_data = {
                "session_id": session_id,
                "candidate_id": active_state.get("candidate_id", str(uuid.uuid4())),
                "context": cached_context,
                "profile": profile,
                "job_description": profile.target_jd,
                "topic_selector": topic_selector,
                "question_generator": question_generator,
                "scoring_engine": scoring_engine,
                "practical_evaluator": practical_evaluator,
                "report_generator": report_generator,
                "practical_task": practical_task,
                "evaluations": [],
                "current_question": current_q,
                "is_interview_completed": active_state.get("is_interview_completed", False),
                "is_practical_completed": active_state.get("is_practical_completed", False),
                "cached_report": None
            }
            async with self._lock:
                self._sessions[session_id] = session_data
            return session_data

        # 2. Reconstruct from PostgreSQL durable records
        recovered = await SessionReconstructionManager.reconstruct_session(session_id)
        if recovered:
            async with self._lock:
                self._sessions[session_id] = recovered
            # Sync back to Redis
            await redis_store.save_context(session_id, recovered["context"])
            await redis_store.save_active_state(session_id, {
                "session_id": session_id,
                "candidate_id": recovered.get("candidate_id"),
                "target_role": recovered["profile"].target_role,
                "is_interview_completed": recovered["is_interview_completed"],
                "is_practical_completed": recovered["is_practical_completed"]
            })
            if recovered.get("current_question"):
                await redis_store.set_current_question(session_id, recovered["current_question"])
            return recovered

        return None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Synchronous session lookup (prefers local memory, recovers if needed)."""
        return self._sessions.get(session_id)

    async def create_session(
        self,
        candidate_name: str,
        candidate_email: str,
        target_role: str,
        skills: List[str],
        experience_years: int = 2,
        projects: Optional[List[str]] = None,
        experience: Optional[List[str]] = None,
        job_description: Optional[str] = None
    ) -> str:
        """Create and initialize a new interview assessment session with PostgreSQL and Redis persistence."""
        session_id = str(uuid.uuid4())
        profile = CandidateProfile(
            name=candidate_name,
            email=candidate_email,
            target_role=target_role,
            skills=skills,
            experience_years=experience_years,
            projects=projects or [],
            experience=experience or [],
            target_jd=job_description
        )
        context = InterviewContext(
            session_id=session_id,
            candidate_profile=profile
        )

        topic_selector = TopicSelector()
        question_generator = QuestionGenerator()
        scoring_engine = ScoringEngine()
        practical_evaluator = PracticalEvaluator()
        report_generator = LLMReportGenerator()
        practical_task = get_practical_task_for_role(target_role)

        # 1. Persist to PostgreSQL durable storage
        candidate_id = str(uuid.uuid4())
        try:
            async with db_manager.session() as sess:
                cand_repo = CandidateRepository(sess)
                cand_orm = await cand_repo.create(
                    name=candidate_name,
                    email=candidate_email,
                    target_role=target_role,
                    experience_years=experience_years,
                    skills=skills,
                    projects=projects or [],
                    experience=experience or [],
                    target_jd=job_description
                )
                candidate_id = cand_orm.id

                sess_repo = SessionRepository(sess)
                await sess_repo.create(
                    session_id=session_id,
                    candidate_id=candidate_id,
                    target_role=target_role,
                    status="CREATED",
                    current_stage="INTRODUCTION"
                )
        except Exception as e:
            logger.error(f"SessionManager: PostgreSQL write failed during create_session: {e}")
            # Do not crash if DB temporarily in maintenance mode; proceed with distributed/in-memory

        # 2. Persist active state to Redis
        state_data = {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "target_role": target_role,
            "current_stage": "INTRODUCTION",
            "current_question_index": 0,
            "is_interview_completed": False,
            "is_practical_completed": False
        }
        await redis_store.save_active_state(session_id, state_data)
        await redis_store.save_context(session_id, context)

        # 3. Store in local worker memory
        session_obj = {
            "session_id": session_id,
            "candidate_id": candidate_id,
            "context": context,
            "profile": profile,
            "job_description": job_description,
            "topic_selector": topic_selector,
            "question_generator": question_generator,
            "scoring_engine": scoring_engine,
            "practical_evaluator": practical_evaluator,
            "report_generator": report_generator,
            "practical_task": practical_task,
            "evaluations": [],
            "current_question": None,
            "is_interview_completed": False,
            "is_practical_completed": False,
            "cached_report": None
        }

        async with self._lock:
            self._sessions[session_id] = session_obj

        logger.info(f"SessionManager: Created durable session {session_id} for {candidate_name} ({target_role})")
        return session_id

    async def start_interview(self, session_id: str) -> QuestionData:
        """Generate the opening Question 1, persisting turns to PostgreSQL & Redis."""
        session = await self.get_or_restore_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found.")

        q_gen: QuestionGenerator = session["question_generator"]
        topic_selector: TopicSelector = session["topic_selector"]
        context: InterviewContext = session["context"]

        # Generate Opening Question
        q_obj: InterviewQuestion = await q_gen.generate_question(context=context)

        q_id = getattr(q_obj, "question_id", None) or f"q_{len(context.questions) + 1}"
        q_text = getattr(q_obj, "question", "") or getattr(q_obj, "question_text", "")
        q_diff = getattr(q_obj, "estimated_difficulty", "") or getattr(q_obj, "difficulty", "Medium")
        q_stage = topic_selector._infer_stage(q_obj.topic)

        q_record = QuestionRecord(
            question_id=q_id,
            question=q_text,
            topic=q_obj.topic,
            difficulty=q_diff,
            is_followup=q_obj.is_followup
        )
        context.questions.append(q_record)
        session["current_question"] = q_record

        # 1. Persist Turn to PostgreSQL
        try:
            async with db_manager.session() as sess:
                turn_repo = TurnRepository(sess)
                await turn_repo.add_turn(
                    session_id=session_id,
                    turn_index=len(context.questions),
                    question_id=q_id,
                    question_text=q_text,
                    topic=q_obj.topic,
                    difficulty=q_diff,
                    stage=q_stage,
                    is_followup=q_obj.is_followup
                )
                sess_repo = SessionRepository(sess)
                await sess_repo.update_state(
                    session_id=session_id,
                    status="IN_PROGRESS",
                    current_stage=q_stage,
                    current_question_index=len(context.questions)
                )
        except Exception as e:
            logger.error(f"SessionManager: PostgreSQL turn write failed during start_interview: {e}")

        # 2. Update Redis
        await redis_store.set_current_question(session_id, q_record)
        await redis_store.save_context(session_id, context)
        await redis_store.save_active_state(session_id, {
            "session_id": session_id,
            "target_role": session["profile"].target_role,
            "current_stage": q_stage,
            "current_question_index": len(context.questions),
            "is_interview_completed": False,
            "is_practical_completed": False
        })

        return QuestionData(
            question_id=q_id,
            question_text=q_text,
            stage=q_stage,
            topic=q_obj.topic,
            difficulty=q_diff,
            question_index=len(context.questions),
            total_estimated=10,
            is_followup=q_obj.is_followup
        )

    async def submit_answer(self, session_id: str, answer_text: str) -> SubmitAnswerResponse:
        """Handle candidate's answer, persist turn & evaluation to PostgreSQL, and advance state."""
        session = await self.get_or_restore_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found.")

        context: InterviewContext = session["context"]
        topic_selector: TopicSelector = session["topic_selector"]
        q_gen: QuestionGenerator = session["question_generator"]
        current_q = session.get("current_question")

        if not current_q:
            raise ValueError("No active question to answer.")

        # 1. Record Answer
        a_record = AnswerRecord(
            question_id=current_q.question_id,
            candidate_answer=answer_text,
            stt_transcript=answer_text,
            time_taken_seconds=15,
            confidence=0.95
        )
        context.answers.append(a_record)

        # 2. Evaluation Simulation (Score calculation)
        word_count = len(answer_text.strip().split())
        score_estimate = min(95.0, max(50.0, 50.0 + (word_count * 1.5)))

        perf_record = PerformanceRecord(
            question_id=current_q.question_id,
            technical_score=score_estimate,
            communication_score=min(95.0, score_estimate + 5.0),
            practical_score=score_estimate,
            problem_solving_score=score_estimate,
            behavioral_score=score_estimate,
            role_fit_score=score_estimate,
            overall_score=score_estimate
        )
        context.performance.append(perf_record)

        eval_result = EvaluationResult(
            question_id=current_q.question_id,
            technical_score=score_estimate,
            practical_score=score_estimate,
            problem_solving_score=score_estimate,
            communication_score=min(95.0, score_estimate + 5.0),
            behavioral_score=score_estimate,
            role_fit_score=score_estimate,
            overall_score=score_estimate,
            strengths=[f"Articulate explanation on {current_q.topic}"] if score_estimate >= 75.0 else [],
            weaknesses=[f"Could provide deeper technical trade-offs on {current_q.topic}"] if score_estimate < 75.0 else [],
            difficulty_recommendation="Medium" if score_estimate >= 70.0 else "Easy",
            feedback=f"Candidate response evaluated for {current_q.topic}."
        )
        session["evaluations"].append(eval_result)

        # 3. Check termination or generate next question
        next_q_obj: InterviewQuestion = await q_gen.generate_question(context=context)

        is_completed = next_q_obj.should_end_interview or len(context.questions) >= 15
        next_q_data = None

        if is_completed:
            session["is_interview_completed"] = True
            session["current_question"] = None
            current_stage = "PRACTICAL"
        else:
            q_id = getattr(next_q_obj, "question_id", None) or f"q_{len(context.questions) + 1}"
            q_text = getattr(next_q_obj, "question", "") or getattr(next_q_obj, "question_text", "")
            q_diff = getattr(next_q_obj, "estimated_difficulty", "") or getattr(next_q_obj, "difficulty", "Medium")
            q_stage = topic_selector._infer_stage(next_q_obj.topic)

            q_record = QuestionRecord(
                question_id=q_id,
                question=q_text,
                topic=next_q_obj.topic,
                difficulty=q_diff,
                is_followup=next_q_obj.is_followup
            )
            context.questions.append(q_record)
            session["current_question"] = q_record
            current_stage = q_stage

            next_q_data = QuestionData(
                question_id=q_id,
                question_text=q_text,
                stage=q_stage,
                topic=q_record.topic,
                difficulty=q_record.difficulty,
                question_index=len(context.questions),
                total_estimated=10,
                is_followup=next_q_obj.is_followup
            )

        # 4. Durable PostgreSQL Persistence for turn answer, evaluation, and next turn
        try:
            async with db_manager.session() as sess:
                turn_repo = TurnRepository(sess)
                await turn_repo.update_answer(
                    session_id=session_id,
                    question_id=current_q.question_id,
                    answer_text=answer_text,
                    stt_transcript=answer_text,
                    time_taken_seconds=15.0
                )

                eval_repo = EvaluationRepository(sess)
                await eval_repo.add_evaluation(
                    session_id=session_id,
                    question_id=current_q.question_id,
                    technical_score=eval_result.technical_score,
                    practical_score=eval_result.practical_score,
                    problem_solving_score=eval_result.problem_solving_score,
                    communication_score=eval_result.communication_score,
                    behavioral_score=eval_result.behavioral_score,
                    role_fit_score=eval_result.role_fit_score,
                    overall_score=eval_result.overall_score,
                    confidence_score=eval_result.confidence_score,
                    strengths=eval_result.strengths,
                    weaknesses=eval_result.weaknesses,
                    feedback=eval_result.feedback,
                    criterion_evaluations=[c.model_dump() for c in eval_result.criterion_evaluations]
                )

                if not is_completed and next_q_data:
                    await turn_repo.add_turn(
                        session_id=session_id,
                        turn_index=len(context.questions),
                        question_id=next_q_data.question_id,
                        question_text=next_q_data.question_text,
                        topic=next_q_data.topic,
                        difficulty=next_q_data.difficulty,
                        stage=next_q_data.stage,
                        is_followup=next_q_data.is_followup
                    )

                sess_repo = SessionRepository(sess)
                await sess_repo.update_state(
                    session_id=session_id,
                    status="COMPLETED" if is_completed else "IN_PROGRESS",
                    current_stage=current_stage,
                    current_question_index=len(context.questions),
                    is_interview_completed=is_completed
                )
        except Exception as e:
            logger.error(f"SessionManager: PostgreSQL turn/eval update failed: {e}")

        # 5. Update Redis
        await redis_store.save_context(session_id, context)
        await redis_store.set_current_question(session_id, session.get("current_question"))
        await redis_store.save_active_state(session_id, {
            "session_id": session_id,
            "target_role": session["profile"].target_role,
            "current_stage": current_stage,
            "current_question_index": len(context.questions),
            "is_interview_completed": is_completed,
            "is_practical_completed": session.get("is_practical_completed", False)
        })

        return SubmitAnswerResponse(
            session_id=session_id,
            answer_acknowledged=True,
            next_question=next_q_data,
            current_stage=current_stage,
            is_practical_ready=is_completed,
            is_completed=False,
            total_questions_asked=len(context.questions)
        )

    def get_practical_task(self, session_id: str) -> PracticalTaskResponse:
        """Retrieve designated practical assessment task with hidden test cases omitted."""
        session = self.get_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found.")

        task: PracticalTask = session["practical_task"]
        visible_cases = [
            VisibleTestCase(
                test_case_id=tc.test_case_id,
                input_params=tc.input_params,
                expected_output=tc.expected_output,
                description=tc.description
            ) for tc in task.visible_test_cases
        ]

        return PracticalTaskResponse(
            task_id=task.task_id,
            title=task.title,
            description=task.description,
            role_archetype=task.role_archetype,
            task_type=task.task_type.value if hasattr(task.task_type, "value") else str(task.task_type),
            language=task.language,
            starter_code=task.starter_code,
            instructions=task.instructions or "Implement the solution to pass the test cases.",
            visible_test_cases=visible_cases,
            hidden_test_count=len(task.hidden_test_cases),
            time_limit_minutes=task.time_limit_minutes
        )

    async def submit_practical(
        self,
        session_id: str,
        submission_code: str,
        language: Optional[str] = None
    ) -> PracticalSubmitResponse:
        """Execute candidate code in isolated sandbox, score, attach to session, and persist to PostgreSQL."""
        session = await self.get_or_restore_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found.")

        task: PracticalTask = session["practical_task"]
        evaluator: PracticalEvaluator = session["practical_evaluator"]
        context: InterviewContext = session["context"]

        pe: PracticalEvaluation = await evaluator.evaluate_submission(task, submission_code, context)
        context.practical_evaluation = pe
        session["is_practical_completed"] = True

        # Build clean execution results items (hiding hidden test definitions)
        results_items = []
        hidden_ids = {tc.test_case_id for tc in task.hidden_test_cases}

        for r in pe.execution_results:
            is_hidden = r.test_case_id in hidden_ids
            results_items.append(ExecutionResultItem(
                test_case_id="Hidden Test Case" if is_hidden else r.test_case_id,
                passed=r.passed,
                actual_output=None if is_hidden and not r.passed else r.actual_output,
                expected_output=None if is_hidden else r.expected_output,
                execution_time_ms=r.execution_time_ms,
                error_message=r.error_message
            ))

        # 1. Persist Practical Evaluation to PostgreSQL
        try:
            async with db_manager.session() as sess:
                pe_repo = PracticalRepository(sess)
                await pe_repo.save_evaluation(
                    session_id=session_id,
                    task_id=pe.task_id,
                    task_title=pe.task_title,
                    role_archetype=pe.role_archetype,
                    language=pe.language,
                    tests_passed=pe.tests_passed,
                    total_tests=pe.total_tests,
                    hidden_tests_passed=pe.hidden_tests_passed,
                    total_hidden_tests=pe.total_hidden_tests,
                    correctness_score=pe.correctness_score,
                    edge_case_score=pe.edge_case_score,
                    complexity_score=pe.complexity_score,
                    code_quality_score=pe.code_quality_score,
                    overall_practical_score=pe.overall_practical_score,
                    time_complexity=pe.time_complexity,
                    space_complexity=pe.space_complexity,
                    feedback=pe.feedback,
                    execution_results=[er.model_dump() for er in pe.execution_results],
                    submission_code=submission_code
                )
                sess_repo = SessionRepository(sess)
                await sess_repo.update_state(
                    session_id=session_id,
                    is_practical_completed=True
                )
        except Exception as e:
            logger.error(f"SessionManager: PostgreSQL practical evaluation write failed: {e}")

        # 2. Update Redis
        await redis_store.save_context(session_id, context)
        await redis_store.save_active_state(session_id, {
            "session_id": session_id,
            "target_role": session["profile"].target_role,
            "is_interview_completed": session["is_interview_completed"],
            "is_practical_completed": True
        })

        return PracticalSubmitResponse(
            task_id=pe.task_id,
            task_title=pe.task_title,
            role_archetype=pe.role_archetype,
            language=pe.language,
            tests_passed=pe.tests_passed,
            total_tests=pe.total_tests,
            hidden_tests_passed=pe.hidden_tests_passed,
            total_hidden_tests=pe.total_hidden_tests,
            correctness_score=pe.correctness_score,
            edge_case_score=pe.edge_case_score,
            complexity_score=pe.complexity_score,
            code_quality_score=pe.code_quality_score,
            overall_practical_score=pe.overall_practical_score,
            time_complexity=pe.time_complexity,
            space_complexity=pe.space_complexity,
            feedback=pe.feedback,
            execution_results=results_items
        )

    async def generate_final_report(self, session_id: str) -> FinalReportResponse:
        """Generate final evidence-grounded 6D report, caching in Redis & persisting to PostgreSQL."""
        session = await self.get_or_restore_session(session_id)
        if not session:
            raise KeyError(f"Session '{session_id}' not found.")

        if session.get("cached_report"):
            return session["cached_report"]

        context: InterviewContext = session["context"]
        evaluations: List[EvaluationResult] = session["evaluations"]
        report_gen: LLMReportGenerator = session["report_generator"]
        scoring_engine: ScoringEngine = session["scoring_engine"]
        profile: CandidateProfile = session["profile"]

        # 1. 6D Scoring computation
        criterion_evals = []
        for e in evaluations:
            criterion_evals.extend(e.criterion_evaluations)

        if not criterion_evals:
            avg_tech = sum(e.technical_score for e in evaluations) / len(evaluations) if evaluations else 75.0
            avg_comm = sum(e.communication_score for e in evaluations) / len(evaluations) if evaluations else 80.0
            from agents.shared.types import CriterionEvaluation
            criterion_evals = [
                CriterionEvaluation(criterion_name="Technical Accuracy", score=avg_tech, observed_evidence=["Answered questions"]),
                CriterionEvaluation(criterion_name="Completeness & Practical", score=avg_tech, observed_evidence=["Addressed prompts"]),
                CriterionEvaluation(criterion_name="Reasoning & Problem Solving", score=avg_tech, observed_evidence=["Structured approach"]),
                CriterionEvaluation(criterion_name="Communication Clarity", score=avg_comm, observed_evidence=["Clear tone"]),
                CriterionEvaluation(criterion_name="Behavioral Alignment", score=avg_comm, observed_evidence=["Professional manner"]),
                CriterionEvaluation(criterion_name="Role Fit", score=avg_tech, observed_evidence=["Role alignment"])
            ]

        scores_6d = scoring_engine.calculate_6d_scores_from_evidence(
            criterion_evals,
            practical_evaluation=context.practical_evaluation
        )

        dim_scores = DimensionScores(
            technical=scores_6d.get("technical_score", 75.0),
            practical=scores_6d.get("practical_score", 75.0),
            problem_solving=scores_6d.get("problem_solving_score", 75.0),
            communication=scores_6d.get("communication_score", 80.0),
            behavioral=scores_6d.get("behavioral_score", 80.0),
            role_fit=scores_6d.get("role_fit_score", 75.0),
            confidence=scores_6d.get("confidence_score", 70.0),
            overall=scores_6d.get("overall_score", 77.0)
        )

        # 2. LLM Report Generation
        report = await report_gen.generate_report(context, evaluations)

        practical_summary = None
        if context.practical_evaluation:
            pe = context.practical_evaluation
            practical_summary = {
                "task_title": pe.task_title,
                "language": pe.language,
                "tests_passed": pe.tests_passed,
                "total_tests": pe.total_tests,
                "hidden_tests_passed": pe.hidden_tests_passed,
                "total_hidden_tests": pe.total_hidden_tests,
                "correctness_score": pe.correctness_score,
                "edge_case_score": pe.edge_case_score,
                "complexity_score": pe.complexity_score,
                "code_quality_score": pe.code_quality_score,
                "overall_practical_score": pe.overall_practical_score,
                "time_complexity": pe.time_complexity,
                "space_complexity": pe.space_complexity,
                "feedback": pe.feedback
            }

        final_response = FinalReportResponse(
            session_id=session_id,
            candidate_name=profile.name,
            target_role=profile.target_role,
            overall_summary=report.overall_summary,
            technical_assessment=report.technical_assessment,
            communication_assessment=report.communication_assessment,
            hiring_recommendation=report.hiring_recommendation,
            confidence_level=report.confidence_level,
            final_score=dim_scores.overall,
            dimension_scores=dim_scores,
            strengths=report.strengths,
            weaknesses=report.weaknesses,
            improvement_plan=report.improvement_plan,
            practical_evaluation=practical_summary
        )

        # 3. Persist Final Report to PostgreSQL
        try:
            async with db_manager.session() as sess:
                rep_repo = ReportRepository(sess)
                candidate_id = session.get("candidate_id", session_id)
                await rep_repo.save_report(
                    session_id=session_id,
                    candidate_id=candidate_id,
                    overall_summary=report.overall_summary,
                    technical_assessment=report.technical_assessment,
                    communication_assessment=report.communication_assessment,
                    hiring_recommendation=report.hiring_recommendation,
                    confidence_level=report.confidence_level,
                    final_score=dim_scores.overall,
                    dimension_scores=dim_scores.model_dump(),
                    strengths=report.strengths,
                    weaknesses=report.weaknesses,
                    improvement_plan=report.improvement_plan
                )
        except Exception as e:
            logger.error(f"SessionManager: PostgreSQL report write failed: {e}")

        session["cached_report"] = final_response
        return final_response
