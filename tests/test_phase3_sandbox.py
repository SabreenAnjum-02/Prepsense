import unittest
import asyncio
import sys
import os
import shutil
import time
from unittest.mock import patch, MagicMock

from agents.shared.types import (
    PracticalTask,
    TestCase,
    TaskType,
    PracticalEvaluation,
    CriterionEvaluation,
    InterviewContext,
    InterviewReport
)
from agents.shared.roles import RoleArchetype
from agents.sandbox.runner import SandboxedCodeRunner
from agents.sandbox.test_engine import TestCaseEngine
from agents.practical.tasks import get_practical_task_for_role, PRACTICAL_TASKS
from agents.practical.evaluator import PracticalEvaluator
from agents.evaluator.scoring import ScoringEngine


class TestPhase3SandboxAndPractical(unittest.TestCase):

    def setUp(self):
        self.runner = SandboxedCodeRunner()
        self.test_engine = TestCaseEngine(self.runner)
        self.evaluator = PracticalEvaluator(self.test_engine)
        self.scoring_engine = ScoringEngine()
        
        # Patch docker if missing, to allow A-K tests to run on host
        if not shutil.which("docker"):
            self.runner.docker_executable = "mock_docker"
            self.original_run_docker = self.runner._run_docker
            
            async def fallback_host_run(image, cmd_args, temp_dir, timeout_seconds, stdin_input):
                exe = sys.executable if "python" in image else "node"
                script_file = cmd_args[-1]
                host_script_path = os.path.join(temp_dir, script_file)
                
                if "python" in image:
                    real_args = [exe, "-u", host_script_path]
                else:
                    real_args = [exe, host_script_path]
                    
                t_start = time.perf_counter()
                try:
                    process = await asyncio.create_subprocess_exec(
                        *real_args,
                        cwd=temp_dir,
                        stdin=asyncio.subprocess.PIPE,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    try:
                        stdout_bytes, stderr_bytes = await asyncio.wait_for(
                            process.communicate(input=stdin_input.encode("utf-8") if stdin_input else None),
                            timeout=timeout_seconds
                        )
                        t_end = time.perf_counter()
                        stdout = stdout_bytes.decode("utf-8", errors="replace")[:65536]
                        stderr = stderr_bytes.decode("utf-8", errors="replace")[:65536]
                        exit_code = process.returncode if process.returncode is not None else 0
                        return {
                            "stdout": stdout, "stderr": stderr, "exit_code": exit_code,
                            "execution_time_ms": round((t_end - t_start) * 1000, 2),
                            "timeout_occurred": False, "security_blocked": False,
                            "error_message": stderr.strip() if exit_code != 0 and stderr else None
                        }
                    except asyncio.TimeoutError:
                        t_end = time.perf_counter()
                        try:
                            process.kill()
                            await process.wait()
                        except Exception:
                            pass
                        return {
                            "stdout": "", "stderr": f"Execution timed out after {timeout_seconds}s.",
                            "exit_code": -1, "execution_time_ms": round((t_end - t_start) * 1000, 2),
                            "timeout_occurred": True, "security_blocked": False,
                            "error_message": f"Time Limit Exceeded ({timeout_seconds}s)"
                        }
                except Exception as e:
                    return {
                        "stdout": "", "stderr": str(e), "exit_code": 1,
                        "execution_time_ms": 0.0, "timeout_occurred": False,
                        "security_blocked": False, "error_message": str(e)
                    }
                    
            self.runner._run_docker = fallback_host_run

    def test_a_python_correct_solution(self):
        """Test A: Correct Python solution passes all visible and hidden test cases."""
        task = PRACTICAL_TASKS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value]
        correct_code = """
def lru_cache_simulation(capacity: int, operations: list) -> list:
    from collections import OrderedDict
    cache = OrderedDict()
    results = []
    for op in operations:
        if op[0] == "put":
            k, v = op[1], op[2]
            if k in cache:
                cache.move_to_end(k)
            cache[k] = v
            if len(cache) > capacity:
                cache.popitem(last=False)
            results.append(None)
        elif op[0] == "get":
            k = op[1]
            if k in cache:
                cache.move_to_end(k)
                results.append(cache[k])
            else:
                results.append(-1)
    return results
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, correct_code))
        print(f"\n[Test A: Python Correct Solution] Tests Passed: {eval_res.tests_passed}/{eval_res.total_tests}")
        self.assertEqual(eval_res.tests_passed, eval_res.total_tests)
        self.assertEqual(eval_res.correctness_score, 100.0)
        self.assertEqual(eval_res.edge_case_score, 100.0)
        self.assertGreaterEqual(eval_res.overall_practical_score, 85.0)

    def test_b_python_incorrect_solution(self):
        """Test B: Incorrect Python solution fails test cases and receives low scores."""
        task = PRACTICAL_TASKS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value]
        incorrect_code = """
def lru_cache_simulation(capacity: int, operations: list) -> list:
    # Always returns wrong answers
    return [0 for _ in operations]
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, incorrect_code))
        print(f"\n[Test B: Python Incorrect Solution] Tests Passed: {eval_res.tests_passed}/{eval_res.total_tests}")
        self.assertEqual(eval_res.tests_passed, 0)
        self.assertEqual(eval_res.correctness_score, 0.0)
        # Anti-inflation check: Cannot exceed 20.0
        self.assertLessEqual(eval_res.overall_practical_score, 20.0)

    def test_c_python_timeout(self):
        """Test C: Infinite loop in Python is terminated safely within timeout."""
        task = PRACTICAL_TASKS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value]
        infinite_loop_code = """
def lru_cache_simulation(capacity: int, operations: list) -> list:
    while True:
        pass
    return []
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, infinite_loop_code))
        print(f"\n[Test C: Python Timeout] Timeout handled safely: {eval_res.tests_passed}/{eval_res.total_tests}")
        self.assertEqual(eval_res.tests_passed, 0)
        self.assertTrue(any(r.timeout_occurred for r in eval_res.execution_results))

    def test_d_python_runtime_error(self):
        """Test D: Python runtime error (ZeroDivisionError) is cleanly caught and reported."""
        task = PRACTICAL_TASKS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value]
        error_code = """
def lru_cache_simulation(capacity: int, operations: list) -> list:
    x = 1 / 0
    return []
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, error_code))
        print(f"\n[Test D: Python Runtime Error] Caught cleanly: {eval_res.execution_results[0].error_message}")
        self.assertEqual(eval_res.tests_passed, 0)
        self.assertIn("ZeroDivisionError", str(eval_res.execution_results[0].error_message))

    def test_e_javascript_correct_solution(self):
        """Test E: Correct JavaScript solution passes all visible and hidden test cases in Node.js."""
        task = PRACTICAL_TASKS[RoleArchetype.FRONTEND_ENGINEER.value]
        correct_js = """
function flattenObject(obj) {
    const result = {};
    function recurse(current, prop) {
        if (Object(current) !== current || Array.isArray(current)) {
            result[prop] = current;
        } else {
            let isEmpty = true;
            for (let p in current) {
                isEmpty = false;
                recurse(current[p], prop ? prop + "." + p : p);
            }
            if (isEmpty && prop) {
                result[prop] = {};
            }
        }
    }
    recurse(obj, "");
    return result;
}
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, correct_js))
        print(f"\n[Test E: JavaScript Correct Solution] Tests Passed: {eval_res.tests_passed}/{eval_res.total_tests}")
        self.assertEqual(eval_res.tests_passed, eval_res.total_tests)
        self.assertEqual(eval_res.correctness_score, 100.0)

    def test_f_javascript_incorrect_solution(self):
        """Test F: Incorrect JavaScript solution fails test cases."""
        task = PRACTICAL_TASKS[RoleArchetype.FRONTEND_ENGINEER.value]
        incorrect_js = """
function flattenObject(obj) {
    return { wrong: true };
}
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, incorrect_js))
        print(f"\n[Test F: JavaScript Incorrect Solution] Tests Passed: {eval_res.tests_passed}/{eval_res.total_tests}")
        self.assertEqual(eval_res.tests_passed, 0)
        self.assertLessEqual(eval_res.overall_practical_score, 20.0)

    def test_g_javascript_timeout(self):
        """Test G: JavaScript infinite loop is terminated safely."""
        task = PRACTICAL_TASKS[RoleArchetype.FRONTEND_ENGINEER.value]
        timeout_js = """
function flattenObject(obj) {
    while (true) {}
}
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, timeout_js))
        print(f"\n[Test G: JavaScript Timeout] Terminated safely: {eval_res.tests_passed}/{eval_res.total_tests}")
        self.assertEqual(eval_res.tests_passed, 0)
        self.assertTrue(any(r.timeout_occurred for r in eval_res.execution_results))

    def test_h_hidden_test_cases_and_edge_cases(self):
        """Test H: Solution passing visible tests but failing hidden edge cases receives partial credit."""
        task = PRACTICAL_TASKS[RoleArchetype.FRONTEND_ENGINEER.value]
        # Partial solution: only handles flat objects or 1 level of nesting, fails deep nesting
        partial_js = """
function flattenObject(obj) {
    if (obj.user && obj.user.name) {
        return { "user.name": obj.user.name, "user.address.city": obj.user.address.city };
    }
    if (obj.a && obj.b) {
        return { a: obj.a, b: obj.b };
    }
    return {};
}
"""
        eval_res: PracticalEvaluation = asyncio.run(self.evaluator.evaluate_submission(task, partial_js))
        print(f"\n[Test H: Partial vs Hidden Tests] Visible Correctness: {eval_res.correctness_score}, Hidden Edge: {eval_res.edge_case_score}")
        self.assertEqual(eval_res.correctness_score, 100.0)  # Passed 2 visible
        self.assertLess(eval_res.edge_case_score, 100.0)      # Failed deep hidden

    def test_i_role_to_assessment_mapping(self):
        """Test I: Every one of the 9 role archetypes maps to a designated, appropriate assessment."""
        for role in RoleArchetype:
            task = get_practical_task_for_role(role.value)
            print(f"Role: {role.value} -> Task: '{task.title}' (Type: {task.task_type.value}, Lang: {task.language})")
            self.assertIsNotNone(task)
            if role in [RoleArchetype.UI_UX_DESIGNER, RoleArchetype.PRODUCT_MANAGER]:
                self.assertIn(task.task_type, [TaskType.UX_DESIGN_CASE, TaskType.PRD_CASE])
            else:
                self.assertIn(task.task_type, [TaskType.CODING, TaskType.INFRA_SCRIPT, TaskType.DATA_ANALYSIS])

    def test_j_practical_scoring_integration(self):
        """Test J: Practical score integrates into 6D scoring and enforces anti-inflation on failure."""
        evals = [
            CriterionEvaluation(criterion_name="Technical Accuracy", score=85.0, observed_evidence=["Solid knowledge"]),
            CriterionEvaluation(criterion_name="Completeness & Coverage", score=80.0, observed_evidence=["Good coverage"]),
            CriterionEvaluation(criterion_name="Reasoning & Problem Solving", score=80.0, observed_evidence=["Sound rationale"]),
            CriterionEvaluation(criterion_name="Communication Clarity", score=90.0, observed_evidence=["Clear"]),
            CriterionEvaluation(criterion_name="Behavioral Alignment", score=85.0, observed_evidence=["STAR format"]),
            CriterionEvaluation(criterion_name="Role Fit", score=85.0, observed_evidence=["Aligned"])
        ]
        
        # 1. Passed Practical Task
        passed_pe = PracticalEvaluation(
            task_id="backend_lru_cache",
            task_title="LRU Cache",
            role_archetype=RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value,
            language="python",
            tests_passed=5,
            total_tests=5,
            correctness_score=100.0,
            edge_case_score=100.0,
            complexity_score=90.0,
            code_quality_score=90.0,
            overall_practical_score=95.0
        )
        scores_pass = self.scoring_engine.calculate_6d_scores_from_evidence(evals, practical_evaluation=passed_pe)
        print(f"\n[Test J1: High Practical Pass] Practical Score: {scores_pass['practical_score']}, Overall: {scores_pass['overall_score']}")
        self.assertGreaterEqual(scores_pass["practical_score"], 85.0)

        # 2. Failed Practical Task (0 tests passed) -> Anti-inflation rule
        failed_pe = PracticalEvaluation(
            task_id="backend_lru_cache",
            task_title="LRU Cache",
            role_archetype=RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value,
            language="python",
            tests_passed=0,
            total_tests=5,
            correctness_score=0.0,
            edge_case_score=0.0,
            complexity_score=40.0,
            code_quality_score=50.0,
            overall_practical_score=10.0
        )
        scores_fail = self.scoring_engine.calculate_6d_scores_from_evidence(evals, practical_evaluation=failed_pe)
        print(f"[Test J2: Failed Practical Execution] Practical Score: {scores_fail['practical_score']}, Overall: {scores_fail['overall_score']}")
        self.assertLessEqual(scores_fail["practical_score"], 25.0)

    def test_k_final_report_integration(self):
        """Test K: Final report schema accommodates practical_evaluation breakdown."""
        pe = PracticalEvaluation(
            task_id="backend_lru_cache",
            task_title="LRU Cache",
            role_archetype="Backend Software Engineer",
            language="python",
            tests_passed=5,
            total_tests=5,
            hidden_tests_passed=3,
            total_hidden_tests=3,
            correctness_score=100.0,
            edge_case_score=100.0,
            complexity_score=90.0,
            code_quality_score=85.0,
            overall_practical_score=93.5,
            time_complexity="O(1)",
            space_complexity="O(capacity)",
            strengths=["Optimal O(1) hashmap + doubly linked list design"],
            feedback="Flawless LRU cache implementation."
        )
        report = InterviewReport(
            session_id="test_session_123",
            overall_summary="Candidate demonstrated exceptional backend architectural depth.",
            technical_assessment="Strong command of caching and data structures.",
            communication_assessment="Clear and articulate.",
            strengths=["System Design", "Python", "Data Structures"],
            weaknesses=[],
            improvement_plan=["Explore distributed consensus protocols."],
            hiring_recommendation="Strong Hire",
            confidence_level="High",
            final_score=91.5,
            practical_evaluation=pe
        )
        self.assertIsNotNone(report.practical_evaluation)
        self.assertEqual(report.practical_evaluation.tests_passed, 5)
        self.assertEqual(report.practical_evaluation.time_complexity, "O(1)")

    def test_l_security_sandbox_escape_prevention(self):
        """Test L: Hostile/untrusted execution attempts (os.system, child_process, sensitive env) are intercepted."""
        # 1. Python forbidden pattern
        bad_python = "import os\nos.system('echo dangerous')"
        res_py = asyncio.run(self.runner.execute_code(bad_python, language="python"))
        print(f"\n[Test L1: Python Security Guard] Blocked: {res_py['security_blocked']}, Msg: {res_py['error_message']}")
        self.assertTrue(res_py["security_blocked"])

        # 2. JavaScript forbidden pattern
        bad_js = "const cp = require('child_process');"
        res_js = asyncio.run(self.runner.execute_code(bad_js, language="javascript"))
        print(f"[Test L2: JavaScript Security Guard] Blocked: {res_js['security_blocked']}, Msg: {res_js['error_message']}")
        self.assertTrue(res_js["security_blocked"])

        # 3. Environment sanitization check
        env_probe_py = """
import os
val = os.environ.get('OPENAI_API_KEY') or os.environ.get('SECRET_KEY') or 'SCRUBBED'
print(val)
"""
        # (check with safety check bypassed on a harmless custom probe)
        safe_env = self.runner._get_isolated_env()
        self.assertNotIn("OPENAI_API_KEY", safe_env)
        self.assertNotIn("SECRET_KEY", safe_env)
        self.assertNotIn("DATABASE_URL", safe_env)



    @patch("asyncio.create_subprocess_exec")
    def test_m_docker_security_flags(self, mock_exec):
        """Test M: Verify that the docker container is invoked with the strict security flags."""
        # Un-patch the mocked run_docker from setUp if it was mocked
        if hasattr(self, "original_run_docker"):
            self.runner._run_docker = self.original_run_docker
        self.runner.docker_executable = "mock_docker"
        
        # Setup mock process
        mock_process = MagicMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_process.returncode = 0
        mock_exec.return_value = mock_process
        
        # Run some simple python code
        asyncio.run(self.runner.execute_code("print('hello')", language="python"))
        
        # Verify the call arguments
        self.assertTrue(mock_exec.called)
        args, kwargs = mock_exec.call_args
        docker_command = list(args)
        
        # Assertions for security boundaries
        self.assertIn("mock_docker", docker_command)
        self.assertIn("run", docker_command)
        self.assertIn("--rm", docker_command)
        self.assertIn("--network=none", docker_command)
        self.assertIn("--memory=256m", docker_command)
        self.assertIn("--cpus=1.0", docker_command)
        self.assertIn("--pids-limit=64", docker_command)
        self.assertIn("--read-only", docker_command)
        self.assertIn("--tmpfs", docker_command)
        
        print("\n[Test M: Docker Sandbox Security Flags] Verified flags: network=none, memory, cpu, pids-limit, read-only")


if __name__ == "__main__":
    unittest.main()

