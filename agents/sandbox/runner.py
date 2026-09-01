import os
import sys
import time
import asyncio
import logging
import aiohttp
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SandboxedCodeRunner:
    """
    Executes untrusted candidate code securely using the public Piston API.
    This eliminates the need for a local Docker-in-Docker setup.
    """
    def __init__(self):
        self.piston_url = "https://emkc.org/api/v2/piston/execute"
        # Map common language names to Piston language identifiers and versions
        self.language_map = {
            "python": {"language": "python", "version": "3.10.0"},
            "py": {"language": "python", "version": "3.10.0"},
            "javascript": {"language": "javascript", "version": "18.15.0"},
            "js": {"language": "javascript", "version": "18.15.0"},
            "node": {"language": "javascript", "version": "18.15.0"},
            "typescript": {"language": "typescript", "version": "5.0.3"},
            "ts": {"language": "typescript", "version": "5.0.3"},
            "java": {"language": "java", "version": "15.0.2"},
            "cpp": {"language": "cpp", "version": "10.2.0"},
            "c++": {"language": "cpp", "version": "10.2.0"}
        }

    async def execute_code(
        self,
        code: str,
        language: str,
        timeout_seconds: float = 5.0,
        stdin_input: str = ""
    ) -> Dict[str, Any]:
        """
        Execute code via Piston API. 
        Matches the return signature expected by the PracticalEvaluator.
        """
        lang_lower = language.lower().strip()
        if lang_lower not in self.language_map:
            return self._build_error(f"Unsupported language for execution API: {language}")

        lang_config = self.language_map[lang_lower]
        
        payload = {
            "language": lang_config["language"],
            "version": lang_config["version"],
            "files": [
                {
                    "content": code
                }
            ],
            "stdin": stdin_input,
            "compile_timeout": int(timeout_seconds * 1000),
            "run_timeout": int(timeout_seconds * 1000)
        }

        t_start = time.perf_counter()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.piston_url, json=payload, timeout=aiohttp.ClientTimeout(total=timeout_seconds + 2.0)) as response:
                    t_end = time.perf_counter()
                    
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Piston API returned {response.status}: {error_text}")
                        return self._build_error(f"Execution service unavailable (HTTP {response.status})")

                    data = await response.json()
                    run_data = data.get("run", {})
                    compile_data = data.get("compile", {})
                    
                    stdout = run_data.get("stdout", "")
                    stderr = run_data.get("stderr", "")
                    exit_code = run_data.get("code", 0)
                    
                    # If compilation failed, attach compile errors
                    if compile_data.get("code", 0) != 0:
                        stderr = compile_data.get("stderr", "") + "\n" + stderr
                        exit_code = compile_data.get("code", 1)

                    is_timeout = run_data.get("signal") == "SIGKILL"
                    
                    return {
                        "stdout": stdout,
                        "stderr": stderr,
                        "exit_code": exit_code if exit_code is not None else 1,
                        "execution_time_ms": round((t_end - t_start) * 1000, 2),
                        "timeout_occurred": is_timeout,
                        "security_blocked": False,
                        "error_message": stderr.strip() if exit_code != 0 and stderr else None,
                    }

        except asyncio.TimeoutError:
            t_end = time.perf_counter()
            return {
                "stdout": "",
                "stderr": f"Execution timed out after {timeout_seconds}s.",
                "exit_code": -1,
                "execution_time_ms": round((t_end - t_start) * 1000, 2),
                "timeout_occurred": True,
                "security_blocked": False,
                "error_message": f"Time Limit Exceeded ({timeout_seconds}s)",
            }
        except Exception as e:
            logger.error(f"Error calling Piston API: {e}")
            return self._build_error(f"Internal execution error: {str(e)}")

    def _build_error(self, message: str) -> Dict[str, Any]:
        return {
            "stdout": "",
            "stderr": message,
            "exit_code": 1,
            "execution_time_ms": 0.0,
            "timeout_occurred": False,
            "security_blocked": False,
            "error_message": message,
        }
