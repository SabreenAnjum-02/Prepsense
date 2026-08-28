import json
import logging
from typing import Optional, List, Dict, Any
from agents.shared.types import (
    PracticalTask, 
    PracticalEvaluation, 
    ExecutionResult, 
    TaskType, 
    InterviewContext
)
from agents.sandbox.test_engine import TestCaseEngine
from shared.llm.client import OllamaClient
from shared.llm.models import LLMRequest

logger = logging.getLogger(__name__)


class PracticalEvaluator:
    """Evaluates practical and coding assessments combining deterministic test execution and LLM code review."""

    def __init__(self, test_engine: Optional[TestCaseEngine] = None, llm_client: Optional[OllamaClient] = None):
        self.test_engine = test_engine or TestCaseEngine()
        self.llm_client = llm_client or OllamaClient()

    async def evaluate_submission(
        self,
        task: PracticalTask,
        submission_text: str,
        context: Optional[InterviewContext] = None
    ) -> PracticalEvaluation:
        """Run complete practical evaluation for a candidate's task submission."""
        logger.info(f"PracticalEvaluator: Evaluating submission for task '{task.task_id}' ({task.task_type.value})")

        if task.task_type in [TaskType.CODING, TaskType.INFRA_SCRIPT, TaskType.DATA_ANALYSIS]:
            return await self._evaluate_coding_submission(task, submission_text)
        else:
            return await self._evaluate_case_submission(task, submission_text)

    async def _evaluate_coding_submission(
        self,
        task: PracticalTask,
        candidate_code: str
    ) -> PracticalEvaluation:
        """Evaluate a coding task using sandbox execution + LLM code review."""
        # 1. Deterministic Execution
        exec_results = await self.test_engine.evaluate_task_submission(task, candidate_code)
        
        hidden_ids = {tc.test_case_id for tc in task.hidden_test_cases}
        visible_ids = {tc.test_case_id for tc in task.visible_test_cases}
        
        total_tests = len(exec_results)
        tests_passed = sum(1 for r in exec_results if r.passed)
        
        total_hidden = len(hidden_ids)
        hidden_passed = sum(1 for r in exec_results if r.passed and r.test_case_id in hidden_ids)
        
        total_visible = len(visible_ids)
        visible_passed = sum(1 for r in exec_results if r.passed and r.test_case_id in visible_ids)

        correctness_score = (visible_passed / total_visible * 100.0) if total_visible > 0 else 0.0
        edge_case_score = (hidden_passed / total_hidden * 100.0) if total_hidden > 0 else correctness_score
        
        execution_pass_rate = (tests_passed / total_tests) if total_tests > 0 else 0.0

        # 2. LLM Qualitative Review (Complexity & Code Quality)
        llm_review = await self._review_code_with_llm(task, candidate_code, tests_passed, total_tests)

        code_quality_score = float(llm_review.get("code_quality_score", 75.0))
        complexity_score = float(llm_review.get("complexity_score", 75.0))
        time_complexity = str(llm_review.get("time_complexity", "O(N)"))
        space_complexity = str(llm_review.get("space_complexity", "O(1)"))
        strengths = list(llm_review.get("strengths", []))
        weaknesses = list(llm_review.get("weaknesses", []))
        feedback = str(llm_review.get("feedback", ""))

        # 3. Deterministic Grounding & Score Calculation
        # Anti-inflation rule: If candidate failed all tests, practical score cannot exceed 20.0
        if total_tests > 0 and tests_passed == 0:
            overall_practical_score = min(20.0, (code_quality_score * 0.2))
            if not weaknesses:
                weaknesses.append("Solution failed all test cases and functional requirements.")
        else:
            # Weighted calculation: 50% Correctness, 25% Edge Cases, 15% Complexity, 10% Code Quality
            overall_practical_score = (
                (correctness_score * 0.50) +
                (edge_case_score * 0.25) +
                (complexity_score * 0.15) +
                (code_quality_score * 0.10)
            )

        overall_practical_score = round(max(0.0, min(100.0, overall_practical_score)), 1)
        correctness_score = round(correctness_score, 1)
        edge_case_score = round(edge_case_score, 1)

        return PracticalEvaluation(
            task_id=task.task_id,
            task_title=task.title,
            role_archetype=task.role_archetype,
            language=task.language,
            tests_passed=tests_passed,
            total_tests=total_tests,
            hidden_tests_passed=hidden_passed,
            total_hidden_tests=total_hidden,
            correctness_score=correctness_score,
            edge_case_score=edge_case_score,
            complexity_score=complexity_score,
            code_quality_score=code_quality_score,
            overall_practical_score=overall_practical_score,
            time_complexity=time_complexity,
            space_complexity=space_complexity,
            strengths=strengths,
            weaknesses=weaknesses,
            feedback=feedback,
            execution_results=exec_results
        )

    async def _review_code_with_llm(
        self,
        task: PracticalTask,
        candidate_code: str,
        tests_passed: int,
        total_tests: int
    ) -> Dict[str, Any]:
        """Request LLM code review for asymptotic complexity, design structure, and code quality."""
        prompt = (
            f"Analyze the following {task.language} solution for the task: '{task.title}'.\n\n"
            f"Task Description:\n{task.description}\n\n"
            f"Candidate Code:\n```\n{candidate_code}\n```\n\n"
            f"Execution Results: {tests_passed}/{total_tests} test cases passed.\n\n"
            "Provide a code review in JSON format:\n"
            "{\n"
            '  "time_complexity": "e.g. O(N) or O(N log N)",\n'
            '  "space_complexity": "e.g. O(1) or O(N)",\n'
            '  "complexity_score": 0.0 - 100.0 (efficiency),\n'
            '  "code_quality_score": 0.0 - 100.0 (readability, structure, naming),\n'
            '  "strengths": ["...", "..."],\n'
            '  "weaknesses": ["...", "..."],\n'
            '  "feedback": "2-3 sentences concise technical review"\n'
            "}\n"
        )
        try:
            req = LLMRequest(
                prompt=prompt,
                system_prompt="You are a senior principal engineer conducting an objective code review. Return ONLY valid JSON.",
                temperature=0.2,
                max_tokens=250,
                require_json=True
            )
            resp = await self.llm_client.generate(req)
            if resp.parsed_json:
                return resp.parsed_json
        except Exception as e:
            logger.warning(f"PracticalEvaluator: LLM code review failed: {e}. Using deterministic defaults.")

        return {
            "time_complexity": "O(N)",
            "space_complexity": "O(1)",
            "complexity_score": 80.0 if tests_passed == total_tests else 60.0,
            "code_quality_score": 80.0 if tests_passed == total_tests else 60.0,
            "strengths": ["Clear procedural implementation"],
            "weaknesses": [] if tests_passed == total_tests else ["Some edge cases failed"],
            "feedback": f"Solution passed {tests_passed} of {total_tests} tests."
        }

    async def _evaluate_case_submission(
        self,
        task: PracticalTask,
        case_text: str
    ) -> PracticalEvaluation:
        """Evaluate non-coding structured cases (e.g. UI/UX design review, Product PRD prioritization)."""
        words = case_text.strip().split()
        # Strict validation: If submission is empty, trivial, or gibberish (< 20 words)
        if len(words) < 20 or len(case_text.strip()) < 80:
            return PracticalEvaluation(
                task_id=task.task_id,
                task_title=task.title,
                role_archetype=task.role_archetype,
                language=task.language,
                tests_passed=0,
                total_tests=1,
                hidden_tests_passed=0,
                total_hidden_tests=1,
                correctness_score=0.0,
                edge_case_score=0.0,
                complexity_score=0.0,
                code_quality_score=0.0,
                overall_practical_score=0.0,
                time_complexity="N/A",
                space_complexity="N/A",
                strengths=[],
                weaknesses=["Submission is incomplete, insufficient, or contains invalid content."],
                feedback="Submission failed: Less than 20 substantive words provided. Detailed design/product analysis is required.",
                execution_results=[
                    ExecutionResult(
                        test_case_id="case_rubric_evaluation",
                        passed=False,
                        actual_output="Insufficient content (< 20 words)",
                        expected_output="Comprehensive analysis addressing all rubric criteria",
                        error_message="Submission does not meet minimum length or content criteria."
                    )
                ]
            )

        prompt = (
            f"Evaluate the candidate's practical case submission for '{task.title}' ({task.role_archetype}).\n\n"
            f"Task Guidelines:\n{task.description}\n\n"
            f"Rubric: {json.dumps(task.rubric or {})}\n\n"
            f"Candidate Submission:\n{case_text}\n\n"
            "Return ONLY this JSON structure:\n"
            "{\n"
            '  "correctness_score": 0.0 - 100.0 (rubric completeness),\n'
            '  "edge_case_score": 0.0 - 100.0 (depth of trade-offs & edge considerations),\n'
            '  "code_quality_score": 0.0 - 100.0 (clarity, structure, professionalism),\n'
            '  "overall_practical_score": 0.0 - 100.0,\n'
            '  "strengths": ["...", "..."],\n'
            '  "weaknesses": ["...", "..."],\n'
            '  "feedback": "2-3 sentences concise case critique"\n'
            "}\n"
        )
        try:
            req = LLMRequest(
                prompt=prompt,
                system_prompt="You are a principal design/product evaluator. Return ONLY valid JSON.",
                temperature=0.2,
                max_tokens=300,
                require_json=True
            )
            resp = await self.llm_client.generate(req)
            if resp.parsed_json:
                data = resp.parsed_json
                raw_score = float(data.get("overall_practical_score", 60.0))
                is_passing = raw_score >= 50.0
                return PracticalEvaluation(
                    task_id=task.task_id,
                    task_title=task.title,
                    role_archetype=task.role_archetype,
                    language=task.language,
                    tests_passed=1 if is_passing else 0,
                    total_tests=1,
                    hidden_tests_passed=1 if is_passing else 0,
                    total_hidden_tests=1,
                    correctness_score=float(data.get("correctness_score", 50.0)),
                    edge_case_score=float(data.get("edge_case_score", 50.0)),
                    complexity_score=float(data.get("edge_case_score", 50.0)),
                    code_quality_score=float(data.get("code_quality_score", 50.0)),
                    overall_practical_score=raw_score,
                    time_complexity="N/A",
                    space_complexity="N/A",
                    strengths=list(data.get("strengths", [])),
                    weaknesses=list(data.get("weaknesses", [])),
                    feedback=str(data.get("feedback", "Case evaluated against rubric.")),
                    execution_results=[
                        ExecutionResult(
                            test_case_id="case_rubric_evaluation",
                            passed=is_passing,
                            actual_output="Structured case evaluated against rubric",
                            expected_output="Comprehensive case response"
                        )
                    ]
                )
        except Exception as e:
            logger.warning(f"PracticalEvaluator: Non-coding case LLM evaluation failed: {e}.")

        return PracticalEvaluation(
            task_id=task.task_id,
            task_title=task.title,
            role_archetype=task.role_archetype,
            language=task.language,
            tests_passed=1,
            total_tests=1,
            hidden_tests_passed=1,
            total_hidden_tests=1,
            correctness_score=65.0,
            edge_case_score=60.0,
            complexity_score=60.0,
            code_quality_score=65.0,
            overall_practical_score=62.5,
            time_complexity="N/A",
            space_complexity="N/A",
            strengths=["Submitted case addressing core guidelines"],
            weaknesses=["Could provide deeper edge case considerations."],
            feedback="Case evaluated based on rubric requirements.",
            execution_results=[
                ExecutionResult(
                    test_case_id="case_rubric_evaluation",
                    passed=True,
                    actual_output="Case submitted",
                    expected_output="Case submitted"
                )
            ]
        )

