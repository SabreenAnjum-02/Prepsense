import asyncio
import logging
import uuid
from typing import List, Optional, Callable
from agents.evaluator.agent import EvaluatorAgent
from agents.shared.types import (
    InterviewQuestion,
    AnswerRecord,
    InterviewContext,
    CandidateProfile
)
from .models import BenchmarkCase, EvaluationPrediction, BenchmarkAnswer

logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """Executes benchmark cases against the existing EvaluatorAgent without bypassing it."""

    def __init__(self, evaluator_agent: Optional[EvaluatorAgent] = None):
        self.evaluator = evaluator_agent or EvaluatorAgent()

    async def evaluate_answer_variant(
        self,
        case: BenchmarkCase,
        answer: BenchmarkAnswer,
        profile: CandidateProfile,
        context: InterviewContext
    ) -> EvaluationPrediction:
        """Runs a single candidate answer variant through the real EvaluatorAgent."""
        q_id = str(uuid.uuid4())
        question_obj = InterviewQuestion(
            question_id=q_id,
            question=case.question,
            topic=case.topic,
            estimated_difficulty=case.estimated_difficulty,
            question_type="Technical" if case.topic != "Behavioral" else "Behavioral",
            is_followup=False,
            expected_topics=case.expected_topics
        )

        answer_record = AnswerRecord(
            question_id=q_id,
            candidate_answer=answer.candidate_answer,
            stt_transcript=answer.candidate_answer,
            time_taken_seconds=45,
            confidence=0.9
        )

        expected_score = answer.expected_scores.overall_score

        try:
            logger.info(f"Runner: Evaluating '{case.case_id}' [{answer.quality_level}]")
            eval_result = await self.evaluator.run({
                "question": question_obj,
                "answer": answer_record,
                "context": context,
                "profile": profile
            })

            if not eval_result:
                raise ValueError("Evaluator returned None (validation failure)")

            predicted_score = float(eval_result.overall_score)
            abs_err = abs(predicted_score - expected_score)
            delta = predicted_score - expected_score

            return EvaluationPrediction(
                case_id=case.case_id,
                topic=case.topic,
                quality_level=answer.quality_level,
                question=case.question,
                candidate_answer=answer.candidate_answer,
                expected_score=expected_score,
                predicted_score=predicted_score,
                absolute_error=abs_err,
                error_delta=delta,
                is_pass_pm1=abs_err <= 1.0,
                is_pass_pm2=abs_err <= 2.0,
                is_pass_pm10=abs_err <= 10.0,
                is_pass_pm20=abs_err <= 20.0,
                predicted_result=eval_result.model_dump(),
                error_message=None
            )

        except Exception as e:
            logger.error(f"Runner: Error evaluating '{case.case_id}' [{answer.quality_level}]: {e}")
            return EvaluationPrediction(
                case_id=case.case_id,
                topic=case.topic,
                quality_level=answer.quality_level,
                question=case.question,
                candidate_answer=answer.candidate_answer,
                expected_score=expected_score,
                predicted_score=0.0,
                absolute_error=expected_score,
                error_delta=-expected_score,
                is_pass_pm1=False,
                is_pass_pm2=False,
                is_pass_pm10=False,
                is_pass_pm20=False,
                predicted_result=None,
                error_message=str(e)
            )

    async def run_benchmark(
        self,
        cases: List[BenchmarkCase],
        progress_callback: Optional[Callable[[int, int, EvaluationPrediction], None]] = None
    ) -> List[EvaluationPrediction]:
        """Executes all benchmark cases sequentially to guarantee 100% local Ollama connection stability."""
        predictions: List[EvaluationPrediction] = []
        
        # Build standard dummy candidate profile & context
        profile = CandidateProfile(
            name="Benchmark Candidate",
            skills=["Python", "Data Structures", "SQL", "Machine Learning", "System Design"],
            experience=["5 years software engineering"]
        )
        context = InterviewContext(
            session_id=str(uuid.uuid4()),
            candidate_profile=profile
        )

        total_evals = sum(len(c.answers) for c in cases)
        completed = 0

        for case in cases:
            for answer in case.answers:
                pred = await self.evaluate_answer_variant(case, answer, profile, context)
                predictions.append(pred)
                completed += 1
                if progress_callback:
                    progress_callback(completed, total_evals, pred)

        return predictions
