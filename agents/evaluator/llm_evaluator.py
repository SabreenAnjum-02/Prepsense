import json
from typing import Optional, Any, List
from agents.shared.types import (
    InterviewQuestion, 
    AnswerRecord, 
    InterviewContext, 
    CandidateProfile,
    EvaluationResult,
    CriterionEvaluation
)
from shared.llm.client import OllamaClient
from shared.llm.models import LLMRequest
from shared.error_handler import with_retry
from .scoring import ScoringEngine
from .utils import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)


class LLMEvaluator:
    """Evidence-based, criterion-driven evaluator using Local LLM for evidence extraction
    and application logic for deterministic weighted scoring.
    """

    def __init__(self, rag_service: Any = None) -> None:
        self.llm_client = OllamaClient()
        self.rag_service = rag_service
        self.scoring_engine = ScoringEngine()

    @with_retry(max_retries=2, delay=1.0)
    async def evaluate(
        self,
        question: InterviewQuestion,
        answer: AnswerRecord,
        context: InterviewContext,
        profile: CandidateProfile
    ) -> EvaluationResult:
        logger.info(f"LLMEvaluator: Extracting evidence & evaluating question {question.question_id}.")
        
        # Retrieve context from RAG
        rag_context_str = ""
        if self.rag_service:
            query = f"{question.topic} {' '.join(question.expected_topics)}"
            logger.info(f"Evaluator querying RAG: '{query}'")
            import time
            from shared.monitor import monitor
            t_rag_start = time.perf_counter()
            results = self.rag_service.query(query, top_k=2)
            t_rag_end = time.perf_counter()
            if context.session_id:
                monitor.record_agent_latency(context.session_id, "RAG_LATENCY", t_rag_end - t_rag_start)
            
            if results:
                rag_context_str = "REFERENCE KNOWLEDGE:\n"
                for res in results:
                    rag_context_str += f"- {res.chunk.content}\n"
                rag_context_str += "\n"

        prompt = (
            "You are an evidence-based technical interviewer evaluating a candidate's answer.\n"
            "Extract evidence and assign accurate ratings (0-100).\n\n"
            "QUESTION DETAILS:\n"
            f"Question: {question.question}\n"
            f"Topic: {question.topic}\n"
            f"Expected Topics: {', '.join(question.expected_topics)}\n"
            f"Difficulty: {question.estimated_difficulty}\n\n"
            "CANDIDATE ANSWER:\n"
            f"{answer.candidate_answer}\n\n"
            f"{rag_context_str}"
            "RULES:\n"
            "1. 'observed_evidence': List correct technical facts explicitly stated by candidate (short phrases).\n"
            "2. 'missing_evidence': List expected topics/concepts the candidate omitted.\n"
            "3. 'incorrect_evidence': List factually false or erroneous statements (empty list if none).\n"
            "4. Scores (0.0 to 100.0): technical_score, completeness_score, reasoning_score, communication_score.\n"
            "5. 'confidence': 'HIGH', 'MEDIUM', or 'LOW'.\n"
            "6. 'feedback': Brief 1-2 sentence constructive feedback.\n\n"
            "Return ONLY JSON:\n"
            "{\n"
            '  "observed_evidence": ["fact 1"],\n'
            '  "missing_evidence": ["omitted concept 1"],\n'
            '  "incorrect_evidence": [],\n'
            '  "technical_score": 75.0,\n'
            '  "completeness_score": 70.0,\n'
            '  "reasoning_score": 75.0,\n'
            '  "communication_score": 80.0,\n'
            '  "confidence": "HIGH",\n'
            '  "feedback": "Short constructive feedback."\n'
            "}\n"
        )
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt="You are an expert technical interviewer. Return compact valid JSON with evidence lists, scores, and short feedback.",
            temperature=0.1,
            max_tokens=300,
            require_json=True
        )
        
        response = await self.llm_client.generate(request)
        
        if not response.parsed_json:
            logger.error("LLM failed to return valid JSON.")
            raise ValueError("Invalid JSON from LLM")

        data = response.parsed_json

        # Extract evidence fields
        observed_ev = data.get("observed_evidence", [])
        missing_ev = data.get("missing_evidence", [])
        incorrect_ev = data.get("incorrect_evidence", [])
        conf_str = str(data.get("confidence", "HIGH")).upper()

        # Extract LLM per-dimension scores (used as informed baseline by ScoringEngine)
        llm_tech = float(data.get("technical_score", 50.0))
        llm_comp = float(data.get("completeness_score", 50.0))
        llm_reas = float(data.get("reasoning_score", 50.0))
        llm_comm = float(data.get("communication_score", 70.0))

        logger.info(f"LLMEvaluator evidence -> observed={len(observed_ev)}, missing={len(missing_ev)}, incorrect={len(incorrect_ev)}, conf={conf_str}")
        logger.info(f"LLMEvaluator LLM scores -> tech={llm_tech}, comp={llm_comp}, reas={llm_reas}, comm={llm_comm}")

        # Build structured CriterionEvaluation models with LLM scores
        criterion_objs: List[CriterionEvaluation] = [
            CriterionEvaluation(
                criterion_name="Technical Correctness & Accuracy",
                expected_evidence=question.expected_topics,
                observed_evidence=observed_ev,
                missing_evidence=missing_ev,
                incorrect_evidence=incorrect_ev,
                score=llm_tech,
                confidence=conf_str,
                reasoning=data.get("feedback", "")
            ),
            CriterionEvaluation(
                criterion_name="Completeness & Depth",
                expected_evidence=question.expected_topics,
                observed_evidence=observed_ev,
                missing_evidence=missing_ev,
                score=llm_comp,
                confidence=conf_str,
                reasoning="Completeness rating"
            ),
            CriterionEvaluation(
                criterion_name="Reasoning & Problem Solving",
                expected_evidence=question.expected_topics,
                observed_evidence=observed_ev,
                missing_evidence=missing_ev,
                score=llm_reas,
                confidence=conf_str,
                reasoning="Problem solving rating"
            ),
            CriterionEvaluation(
                criterion_name="Communication Quality",
                observed_evidence=observed_ev if observed_ev else ["Clear answer structure"],
                score=llm_comm,
                confidence=conf_str,
                reasoning="Communication rating"
            )
        ]

        # Application-side deterministic 6D weighted score calculation
        scores_6d = self.scoring_engine.calculate_6d_scores_from_evidence(criterion_objs)
        tech_score = scores_6d["technical_score"]
        prac_score = scores_6d["practical_score"]
        prob_score = scores_6d["problem_solving_score"]
        comm_score = scores_6d["communication_score"]
        behav_score = scores_6d["behavioral_score"]
        role_fit_score = scores_6d["role_fit_score"]
        conf_score = scores_6d["confidence_score"]
        overall_score = scores_6d["overall_score"]

        strengths = data.get("strengths") or observed_ev[:3]
        weaknesses = data.get("weaknesses") or (missing_ev[:2] + incorrect_ev[:2])
        expected_topics_covered = data.get("expected_topics_covered") or observed_ev[:3]
        missing_topics = data.get("missing_topics") or missing_ev[:3]

        try:
            result = EvaluationResult(
                question_id=question.question_id,
                technical_score=tech_score,
                practical_score=prac_score,
                problem_solving_score=prob_score,
                communication_score=comm_score,
                behavioral_score=behav_score,
                role_fit_score=role_fit_score,
                reasoning_score=prob_score,
                confidence_score=conf_score,
                overall_score=overall_score,
                strengths=strengths,
                weaknesses=weaknesses,
                expected_topics_covered=expected_topics_covered,
                missing_topics=missing_topics,
                difficulty_recommendation=data.get("difficulty_recommendation", "Medium"),
                feedback=data.get("feedback", "Answer evaluated successfully."),
                criterion_evaluations=criterion_objs
            )
            return result

        except ValidationError as e:
            logger.error(f"Evaluator output failed validation: {e}")
            raise ValueError(f"Validation failed: {e}")
