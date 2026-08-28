import json
from typing import List
from agents.shared.types import (
    InterviewContext,
    EvaluationResult,
    InterviewReport
)
from shared.llm.client import OllamaClient
from shared.llm.models import LLMRequest
from shared.error_handler import with_retry
from .utils import get_logger
from pydantic import ValidationError

logger = get_logger(__name__)

class LLMReportGenerator:
    def __init__(self) -> None:
        self.llm_client = OllamaClient()

    @with_retry(max_retries=2, delay=1.0)
    async def generate_report(
        self,
        context: InterviewContext,
        evaluations: List[EvaluationResult]
    ) -> InterviewReport:
        logger.info(f"Generating report for session {context.session_id} using LLM provider.")
        
        # Calculate some aggregates to help the LLM
        if evaluations:
            avg_tech = sum(e.technical_score for e in evaluations) / len(evaluations)
            avg_comm = sum(e.communication_score for e in evaluations) / len(evaluations)
            avg_overall = sum(e.overall_score for e in evaluations) / len(evaluations)
        else:
            avg_tech = avg_comm = avg_overall = 0.0
            
        # Build concise evaluation summaries to prevent prompt bloat and timeouts
        concise_evals = []
        for idx, e in enumerate(evaluations, 1):
            concise_evals.append({
                "question_num": idx,
                "technical_score": round(e.technical_score, 1),
                "communication_score": round(e.communication_score, 1),
                "overall_score": round(e.overall_score, 1),
                "strengths": e.strengths,
                "weaknesses": e.weaknesses,
                "feedback": e.feedback
            })

        cand = context.candidate_profile
        target_role = cand.target_role if cand and cand.target_role else "Software Engineer"
        target_jd = cand.target_jd if cand and cand.target_jd else "Standard industry role blueprint requirements"
        candidate_name = cand.name if cand else "Candidate"
        skills_str = ", ".join(cand.skills) if cand and cand.skills else "General software skills"

        # Build concise Q&A transcript
        qa_transcript = []
        for idx, q in enumerate(context.questions, 1):
            ans = next((a.candidate_answer for a in context.answers if a.question_id == q.question_id), "No response recorded")
            qa_transcript.append({
                "question_num": idx,
                "topic": q.topic,
                "question": q.question,
                "candidate_answer": ans[:200] + "..." if len(ans) > 200 else ans
            })

        # Include Practical Assessment Summary if available
        practical_summary = "None conducted."
        if context.practical_evaluation:
            pe = context.practical_evaluation
            practical_summary = (
                f"Task: {pe.task_title} ({pe.language})\n"
                f"Tests Passed: {pe.tests_passed}/{pe.total_tests} (Hidden Tests: {pe.hidden_tests_passed}/{pe.total_hidden_tests})\n"
                f"Correctness Score: {pe.correctness_score}/100, Edge-Case Score: {pe.edge_case_score}/100\n"
                f"Complexity: Time {pe.time_complexity}, Space {pe.space_complexity} (Score: {pe.complexity_score}/100)\n"
                f"Code Quality Score: {pe.code_quality_score}/100\n"
                f"Overall Practical Score: {pe.overall_practical_score}/100\n"
                f"Feedback: {pe.feedback}"
            )

        prompt = (
            f"You are a Senior Hiring Principal and Technical Assessment Director evaluating {candidate_name} for the position of {target_role}.\n\n"
            "CANDIDATE & ROLE CONTEXT:\n"
            f"- Candidate: {candidate_name}\n"
            f"- Target Role: {target_role}\n"
            f"- Resume Skills: {skills_str}\n"
            f"- Job Description Requirements: {target_jd[:300]}\n\n"
            "EVALUATION AGGREGATES:\n"
            f"- Average Technical Score: {avg_tech:.1f}/100\n"
            f"- Average Communication Score: {avg_comm:.1f}/100\n"
            f"- Average Overall Score: {avg_overall:.1f}/100\n\n"
            f"PRACTICAL CODING / CASE PERFORMANCE:\n{practical_summary}\n\n"
            f"INTERVIEW QUESTIONS & CANDIDATE TRANSCRIPT:\n"
            f"{json.dumps(qa_transcript, indent=2)}\n\n"
            "EVALUATION INSTRUCTIONS:\n"
            f"1. Generate a rigorous, evidence-grounded assessment specific to {target_role}.\n"
            "2. Cite actual examples and quotes from the candidate's answers.\n"
            "3. Provide realistic strengths, actionable skill gaps, and a concrete 3-step improvement roadmap.\n"
            "4. Assign a decisive hiring recommendation: 'Strong Hire', 'Hire', 'Borderline', or 'No Hire'.\n\n"
            "You MUST return a strictly valid JSON object matching this structure:\n"
            "{\n"
            '  "session_id": "' + str(context.session_id) + '",\n'
            '  "overall_summary": "Comprehensive 3-4 sentence performance summary grounded in candidate evidence",\n'
            '  "technical_assessment": "Detailed 2-3 sentence domain-specific evaluation of candidate architecture/syntax depth",\n'
            '  "communication_assessment": "2-3 sentence evaluation of clarity, trade-off articulation, and STAR structure",\n'
            '  "strengths": ["Evidence-backed strength 1", "Evidence-backed strength 2", "Evidence-backed strength 3"],\n'
            '  "weaknesses": ["Specific skill gap 1", "Specific skill gap 2"],\n'
            '  "improvement_plan": ["Actionable step 1", "Actionable step 2", "Actionable step 3"],\n'
            '  "hiring_recommendation": "Strong Hire | Hire | Borderline | No Hire",\n'
            '  "confidence_level": "High | Medium | Low",\n'
            f'  "final_score": {avg_overall:.1f}\n'
            "}\n"
        )
        
        request = LLMRequest(
            prompt=prompt,
            system_prompt=f"You are an expert technical hiring manager evaluating a {target_role} candidate. Return ONLY valid JSON.",
            temperature=0.25,
            max_tokens=450,
            require_json=True
        )
        
        response = await self.llm_client.generate(request)
        
        if not response.parsed_json:
            logger.error("LLM failed to return valid JSON.")
            raise ValueError("Invalid JSON from LLM")
            
        try:
            report = InterviewReport(**response.parsed_json)
            report.session_id = context.session_id
            report.practical_evaluation = context.practical_evaluation
            return report
        except ValidationError as e:
            logger.error(f"Report LLM output failed validation: {e}")
            raise ValueError(f"Validation failed: {e}")

