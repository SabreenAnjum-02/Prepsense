import json
import logging
from typing import List, Dict, Any, Optional
from agents.shared.types import TestCase, ExecutionResult, PracticalTask
from .runner import SandboxedCodeRunner

logger = logging.getLogger(__name__)


class TestCaseEngine:
    """Evaluates candidate code submissions against visible and hidden test cases in the sandbox."""

    def __init__(self, runner: Optional[SandboxedCodeRunner] = None):
        self.runner = runner or SandboxedCodeRunner()

    def _build_python_harness(
        self,
        candidate_code: str,
        function_name: str,
        test_cases: List[TestCase]
    ) -> str:
        """Construct a Python execution harness that executes all test cases and emits structured JSON."""
        # Convert test cases into JSON structure
        cases_payload = []
        for tc in test_cases:
            cases_payload.append({
                "test_case_id": tc.test_case_id,
                "input_params": tc.input_params,
                "expected_output": tc.expected_output,
                "is_hidden": tc.is_hidden
            })

        cases_json_literal = json.dumps(json.dumps(cases_payload))

        harness = f"""import sys
import json
import time

# --- Candidate Solution ---
{candidate_code}

# --- Test Execution Harness ---
def _run_all_tests():
    test_cases = json.loads({cases_json_literal})
    results = []
    
    for tc in test_cases:
        tc_id = tc["test_case_id"]
        inp = tc["input_params"]
        exp = tc["expected_output"]
        is_hidden = tc["is_hidden"]
        
        t0 = time.perf_counter()
        passed = False
        actual = None
        err_msg = None
        
        try:
            func = globals().get("{function_name}")
            if not func or not callable(func):
                err_msg = f"Function '{function_name}' not defined or callable."
            else:
                if isinstance(inp, dict):
                    actual = func(**inp)
                elif isinstance(inp, list):
                    actual = func(*inp)
                else:
                    actual = func(inp)
                
                # Check equality (deep comparison or json-compatible comparison)
                if actual == exp:
                    passed = True
                elif isinstance(actual, (list, tuple)) and isinstance(exp, (list, tuple)) and list(actual) == list(exp):
                    passed = True
                elif isinstance(actual, float) and isinstance(exp, (int, float)) and abs(actual - exp) < 1e-4:
                    passed = True
                else:
                    passed = False
                    
        except Exception as e:
            err_msg = f"{{type(e).__name__}}: {{str(e)}}"
            passed = False
            
        t1 = time.perf_counter()
        
        results.append({{
            "test_case_id": tc_id,
            "passed": passed,
            "actual_output": None if is_hidden and not passed else actual,
            "expected_output": None if is_hidden else exp,
            "execution_time_ms": round((t1 - t0) * 1000, 2),
            "error_message": err_msg,
            "is_hidden": is_hidden
        }})
        
    print("__PREPSENSE_RESULTS_START__")
    print(json.dumps(results))
    print("__PREPSENSE_RESULTS_END__")

if __name__ == "__main__":
    _run_all_tests()
"""
        return harness

    def _build_javascript_harness(
        self,
        candidate_code: str,
        function_name: str,
        test_cases: List[TestCase]
    ) -> str:
        """Construct a JavaScript (Node.js) execution harness that executes all test cases and emits JSON."""
        cases_payload = []
        for tc in test_cases:
            cases_payload.append({
                "test_case_id": tc.test_case_id,
                "input_params": tc.input_params,
                "expected_output": tc.expected_output,
                "is_hidden": tc.is_hidden
            })

        harness = f"""
// --- Candidate Solution ---
{candidate_code}

// --- Test Execution Harness ---
function _deepEqual(a, b) {{
    if (a === b) return true;
    if (typeof a === 'number' && typeof b === 'number' && Math.abs(a - b) < 1e-4) return true;
    if (typeof a !== 'object' || a === null || typeof b !== 'object' || b === null) return false;
    let keysA = Object.keys(a), keysB = Object.keys(b);
    if (keysA.length !== keysB.length) return false;
    for (let key of keysA) {{
        if (!keysB.includes(key) || !_deepEqual(a[key], b[key])) return false;
    }}
    return true;
}}

function _runAllTests() {{
    const testCases = {json.dumps(cases_payload)};
    const results = [];
    
    for (let tc of testCases) {{
        const tcId = tc.test_case_id;
        const inp = tc.input_params;
        const exp = tc.expected_output;
        const isHidden = tc.is_hidden;
        
        let passed = false;
        let actual = null;
        let errMsg = null;
        let t0 = Date.now();
        
        try {{
            if (typeof {function_name} !== 'function') {{
                errMsg = "Function '{function_name}' is not defined.";
            }} else {{
                if (Array.isArray(inp)) {{
                    actual = {function_name}(...inp);
                }} else {{
                    actual = {function_name}(inp);
                }}
                passed = _deepEqual(actual, exp);
            }}
        }} catch (err) {{
            errMsg = err.toString();
            passed = false;
        }}
        let t1 = Date.now();
        
        results.push({{
            test_case_id: tcId,
            passed: passed,
            actual_output: isHidden && !passed ? null : actual,
            expected_output: isHidden ? null : exp,
            execution_time_ms: t1 - t0,
            error_message: errMsg,
            is_hidden: isHidden
        }});
    }}
    
    console.log("__PREPSENSE_RESULTS_START__");
    console.log(JSON.stringify(results));
    console.log("__PREPSENSE_RESULTS_END__");
}}

_runAllTests();
"""
        return harness

    async def evaluate_task_submission(
        self,
        task: PracticalTask,
        candidate_code: str,
        timeout_seconds: Optional[float] = None
    ) -> List[ExecutionResult]:
        """Execute all visible and hidden test cases for a task submission."""
        all_test_cases = list(task.visible_test_cases) + list(task.hidden_test_cases)
        if not all_test_cases:
            # Fallback: simple execution run
            exec_res = await self.runner.execute_code(
                candidate_code,
                language=task.language,
                timeout_seconds=timeout_seconds or 5.0
            )
            return [
                ExecutionResult(
                    test_case_id="default_run",
                    passed=exec_res["exit_code"] == 0,
                    stdout=exec_res["stdout"],
                    stderr=exec_res["stderr"],
                    execution_time_ms=exec_res["execution_time_ms"],
                    error_message=exec_res["error_message"],
                    timeout_occurred=exec_res["timeout_occurred"]
                )
            ]

        func_name = task.function_name or "solution"
        lang_lower = task.language.lower()
        max_timeout = timeout_seconds or min(8.0, max(4.0, sum(tc.timeout_seconds for tc in all_test_cases) * 0.8))

        if lang_lower in ["python", "py"]:
            harness_code = self._build_python_harness(candidate_code, func_name, all_test_cases)
        elif lang_lower in ["javascript", "js", "node", "typescript", "ts"]:
            harness_code = self._build_javascript_harness(candidate_code, func_name, all_test_cases)
        else:
            return [
                ExecutionResult(
                    test_case_id=tc.test_case_id,
                    passed=False,
                    expected_output=tc.expected_output,
                    error_message=f"Unsupported language: {task.language}"
                ) for tc in all_test_cases
            ]

        # Execute in sandbox
        exec_res = await self.runner.execute_code(
            harness_code,
            language=task.language,
            timeout_seconds=max_timeout
        )

        if exec_res["timeout_occurred"]:
            logger.warning(f"TestCaseEngine: Assessment execution timed out after {max_timeout}s.")
            return [
                ExecutionResult(
                    test_case_id=tc.test_case_id,
                    passed=False,
                    expected_output=None if tc.is_hidden else tc.expected_output,
                    error_message=f"Time Limit Exceeded ({max_timeout}s)",
                    timeout_occurred=True,
                    execution_time_ms=exec_res["execution_time_ms"]
                ) for tc in all_test_cases
            ]

        if exec_res["security_blocked"]:
            logger.warning(f"TestCaseEngine: Assessment execution blocked by security policy: {exec_res['error_message']}")
            return [
                ExecutionResult(
                    test_case_id=tc.test_case_id,
                    passed=False,
                    expected_output=None if tc.is_hidden else tc.expected_output,
                    error_message=exec_res["error_message"],
                    stderr=exec_res["stderr"]
                ) for tc in all_test_cases
            ]

        # Parse test results from stdout delimiter
        stdout = exec_res["stdout"]
        start_marker = "__PREPSENSE_RESULTS_START__"
        end_marker = "__PREPSENSE_RESULTS_END__"

        if start_marker in stdout and end_marker in stdout:
            try:
                json_str = stdout.split(start_marker)[1].split(end_marker)[0].strip()
                raw_results = json.loads(json_str)
                results = []
                for r in raw_results:
                    results.append(ExecutionResult(
                        test_case_id=r["test_case_id"],
                        passed=r["passed"],
                        actual_output=r.get("actual_output"),
                        expected_output=r.get("expected_output"),
                        stdout=stdout,
                        stderr=exec_res["stderr"],
                        execution_time_ms=r.get("execution_time_ms", 0.0),
                        error_message=r.get("error_message"),
                        timeout_occurred=False
                    ))
                return results
            except Exception as e:
                logger.error(f"TestCaseEngine: Failed to parse harness results: {e}")

        # If execution crashed before outputting results (e.g. syntax error or top-level exception)
        err = exec_res["error_message"] or exec_res["stderr"] or "Execution failed without test output."
        return [
            ExecutionResult(
                test_case_id=tc.test_case_id,
                passed=False,
                expected_output=None if tc.is_hidden else tc.expected_output,
                stdout=exec_res["stdout"],
                stderr=exec_res["stderr"],
                execution_time_ms=exec_res["execution_time_ms"],
                error_message=err.splitlines()[-1] if err else "Execution Error",
                timeout_occurred=False
            ) for tc in all_test_cases
        ]

