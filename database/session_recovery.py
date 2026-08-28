import logging
from typing import Optional, Dict, Any, List

from .connection import db_manager
from .repository import (
    CandidateRepository,
    SessionRepository,
    TurnRepository,
    EvaluationRepository,
    PracticalRepository,
    ReportRepository
)
from agents.shared.types import (
    CandidateProfile,
    InterviewContext,
    QuestionRecord,
    AnswerRecord,
    PerformanceRecord,
    EvaluationResult,
    CriterionEvaluation,
    PracticalEvaluation,
    ExecutionResult
)
from agents.planner.topic_selector import TopicSelector
from agents.interviewer.generator import QuestionGenerator
from agents.evaluator.scoring import ScoringEngine
from agents.practical.tasks import get_practical_task_for_role
from agents.practical.evaluator import PracticalEvaluator
from agents.report.llm_report_generator import LLMReportGenerator

logger = logging.getLogger(__name__)


class SessionReconstructionManager:
    """Recovers and hydrates full interview sessions from PostgreSQL durable storage."""

    @staticmethod
    async def reconstruct_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Hydrate complete session state from PostgreSQL durable records across node restarts."""
        async with db_manager.session() as sess:
            session_repo = SessionRepository(sess)
            session_orm = await session_repo.get_by_id(session_id, include_relations=True)
            if not session_orm:
                return None

            cand_orm = session_orm.candidate
            profile = CandidateProfile(
                name=cand_orm.name,
                email=cand_orm.email,
                target_role=cand_orm.target_role,
                skills=cand_orm.skills or [],
                experience_years=cand_orm.experience_years,
                projects=cand_orm.projects or [],
                experience=cand_orm.experience or [],
                target_jd=cand_orm.target_jd
            )

            context = InterviewContext(
                session_id=session_id,
                candidate_profile=profile
            )

            # Reconstruct questions and answers from turns
            current_q_record = None
            for turn in sorted(session_orm.turns, key=lambda t: t.turn_index):
                q_rec = QuestionRecord(
                    question_id=turn.question_id,
                    question=turn.question_text,
                    topic=turn.topic,
                    difficulty=turn.difficulty,
                    is_followup=turn.is_followup
                )
                context.questions.append(q_rec)
                current_q_record = q_rec

                if turn.candidate_answer:
                    a_rec = AnswerRecord(
                        question_id=turn.question_id,
                        candidate_answer=turn.candidate_answer,
                        stt_transcript=turn.stt_transcript or turn.candidate_answer,
                        time_taken_seconds=turn.time_taken_seconds or 15,
                        confidence=0.95
                    )
                    context.answers.append(a_rec)

            # Reconstruct evaluations and performance records
            evaluations: List[EvaluationResult] = []
            for ev_orm in session_orm.evaluations:
                perf_rec = PerformanceRecord(
                    question_id=ev_orm.question_id,
                    technical_score=ev_orm.technical_score,
                    practical_score=ev_orm.practical_score,
                    problem_solving_score=ev_orm.problem_solving_score,
                    communication_score=ev_orm.communication_score,
                    behavioral_score=ev_orm.behavioral_score,
                    role_fit_score=ev_orm.role_fit_score,
                    overall_score=ev_orm.overall_score
                )
                context.performance.append(perf_rec)

                crit_evals = []
                for c in (ev_orm.criterion_evaluations or []):
                    try:
                        crit_evals.append(CriterionEvaluation.model_validate(c))
                    except Exception:
                        pass

                eval_res = EvaluationResult(
                    question_id=ev_orm.question_id,
                    technical_score=ev_orm.technical_score,
                    practical_score=ev_orm.practical_score,
                    problem_solving_score=ev_orm.problem_solving_score,
                    communication_score=ev_orm.communication_score,
                    behavioral_score=ev_orm.behavioral_score,
                    role_fit_score=ev_orm.role_fit_score,
                    overall_score=ev_orm.overall_score,
                    confidence_score=ev_orm.confidence_score,
                    strengths=ev_orm.strengths or [],
                    weaknesses=ev_orm.weaknesses or [],
                    difficulty_recommendation="Medium",
                    feedback=ev_orm.feedback or "",
                    criterion_evaluations=crit_evals
                )
                evaluations.append(eval_res)

            # Reconstruct practical evaluation if present
            if session_orm.practical_evaluation:
                pe_orm = session_orm.practical_evaluation
                exec_results = []
                for ex in (pe_orm.execution_results or []):
                    try:
                        exec_results.append(ExecutionResult.model_validate(ex))
                    except Exception:
                        pass

                pe = PracticalEvaluation(
                    task_id=pe_orm.task_id,
                    task_title=pe_orm.task_title,
                    role_archetype=pe_orm.role_archetype,
                    language=pe_orm.language,
                    tests_passed=pe_orm.tests_passed,
                    total_tests=pe_orm.total_tests,
                    hidden_tests_passed=pe_orm.hidden_tests_passed,
                    total_hidden_tests=pe_orm.total_hidden_tests,
                    correctness_score=pe_orm.correctness_score,
                    edge_case_score=pe_orm.edge_case_score,
                    complexity_score=pe_orm.complexity_score,
                    code_quality_score=pe_orm.code_quality_score,
                    overall_practical_score=pe_orm.overall_practical_score,
                    time_complexity=pe_orm.time_complexity,
                    space_complexity=pe_orm.space_complexity,
                    feedback=pe_orm.feedback or "",
                    execution_results=exec_results
                )
                context.practical_evaluation = pe

            # Instantiate agent instances
            topic_selector = TopicSelector()
            question_generator = QuestionGenerator()
            scoring_engine = ScoringEngine()
            practical_evaluator = PracticalEvaluator()
            report_generator = LLMReportGenerator()
            practical_task = get_practical_task_for_role(cand_orm.target_role)

            hydrated = {
                "session_id": session_id,
                "context": context,
                "profile": profile,
                "job_description": cand_orm.target_jd,
                "topic_selector": topic_selector,
                "question_generator": question_generator,
                "scoring_engine": scoring_engine,
                "practical_evaluator": practical_evaluator,
                "report_generator": report_generator,
                "practical_task": practical_task,
                "evaluations": evaluations,
                "current_question": current_q_record if not session_orm.is_interview_completed else None,
                "is_interview_completed": session_orm.is_interview_completed,
                "is_practical_completed": session_orm.is_practical_completed,
                "cached_report": None
            }

            logger.info(f"SessionRecovery: Successfully recovered session {session_id} from PostgreSQL ({len(context.questions)} questions, {len(context.answers)} answers)")
            return hydrated
