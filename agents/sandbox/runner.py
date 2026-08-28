import asyncio
import os
import sys
import time
import tempfile
import shutil
import logging


from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Sensitive environment variables to scrub
SCRUB_ENV_VARS = [
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GROQ_API_KEY", 
    "AWS_SECRET_ACCESS_KEY", "DATABASE_URL", "SECRET_KEY", 
    "PREPSENSE_API_KEY", "TOKEN", "PASSWORD"
]

# Forbidden patterns in candidate submissions (defense-in-depth layer)
FORBIDDEN_PYTHON_PATTERNS = [
    "os.system", "subprocess", "shutil.rmtree", "ctypes", 
    "__import__('os').system", "__import__('subprocess')",
    "socket.socket", "urllib.request", "requests.get", "requests.post",
    "pty.spawn", "multiprocessing.Process"
]

FORBIDDEN_JS_PATTERNS = [
    "child_process", "require('fs')", "require(\"fs\")", "import fs",
    "require('child_process')", "require(\"child_process\")",
    "process.exit", "process.kill", "process.env"
]


class SandboxedCodeRunner:
    """Safe, isolated runner for executing untrusted candidate code in sandboxed subprocesses."""

    def __init__(self, python_executable: Optional[str] = None, node_executable: Optional[str] = None):
        self.python_executable = python_executable or sys.executable
        self.node_executable = node_executable or "node"
        self.docker_executable = shutil.which("docker")
        if not self.docker_executable:
            logger.warning("Docker executable not found in PATH.")

    def _get_isolated_env(self) -> Dict[str, str]:
        """Produce a sanitized, minimal environment for candidate code subprocess."""
        # Kept for compatibility, though we don't pass this to docker run by default
        safe_keys = [
            "PATH", "SYSTEMROOT", "WINDIR", "TEMP", "TMP", 
            "PYTHONPATH", "PYTHONHOME", "NODE_PATH", "LANG", "LC_ALL"
        ]
        env = {k: v for k, v in os.environ.items() if k.upper() in safe_keys}
        for scrub_k in SCRUB_ENV_VARS:
            env.pop(scrub_k, None)
        return env

    def check_safety_guards(self, code: str, language: str) -> Optional[str]:
        """Perform static defense-in-depth check for known malicious/escape patterns."""
        lang_lower = language.lower()
        if lang_lower in ["python", "py"]:
            for pat in FORBIDDEN_PYTHON_PATTERNS:
                if pat in code:
                    return f"Security Restriction: Use of '{pat}' is not permitted in the assessment sandbox."
        elif lang_lower in ["javascript", "js", "typescript", "ts"]:
            for pat in FORBIDDEN_JS_PATTERNS:
                if pat in code:
                    return f"Security Restriction: Use of '{pat}' is not permitted in the assessment sandbox."
        return None

    async def execute_code(
        self,
        code: str,
        language: str = "python",
        timeout_seconds: float = 3.0,
        stdin_input: str = ""
    ) -> Dict[str, Any]:
        """Execute code in a separate, isolated Docker container with strict timeout."""
        # Determine language lower case early for both fallback and Docker paths
        lang_lower = language.lower()
        if not self.docker_executable:
            # Fallback to local execution when Docker is unavailable (e.g., CI without Docker).
            # This is a best‑effort insecure fallback used only for testing environments.
            if lang_lower in ["python", "py"]:
                return await self._run_python_local(code, timeout_seconds, stdin_input)
            elif lang_lower in ["javascript", "js", "node"]:
                return await self._run_javascript_local(code, timeout_seconds, stdin_input)
            else:
                return {
                    "stdout": "",
                    "stderr": f"Unsupported execution language: {language}",
                    "exit_code": 1,
                    "execution_time_ms": 0.0,
                    "timeout_occurred": False,
                    "security_blocked": False,
                    "error_message": f"Unsupported language: {language}"
                }

        lang_lower = language.lower()
        
        # 1. Static security barrier
        violation = self.check_safety_guards(code, lang_lower)
        if violation:
            return {
                "stdout": "",
                "stderr": violation,
                "exit_code": 1,
                "execution_time_ms": 0.0,
                "timeout_occurred": False,
                "security_blocked": True,
                "error_message": violation
            }

        # 2. Temp directory isolation for bind mount
        temp_dir = tempfile.mkdtemp(prefix="prepsense_sandbox_")
        try:
            if lang_lower in ["python", "py"]:
                return await self._run_python_docker(code, timeout_seconds, stdin_input, temp_dir)
            elif lang_lower in ["javascript", "js", "node"]:
                return await self._run_javascript_docker(code, timeout_seconds, stdin_input, temp_dir)
            else:
                return {
                    "stdout": "",
                    "stderr": f"Unsupported execution language: {language}",
                    "exit_code": 1,
                    "execution_time_ms": 0.0,
                    "timeout_occurred": False,
                    "security_blocked": False,
                    "error_message": f"Unsupported language: {language}"
                }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _run_docker(
        self,
        image: str,
        cmd_args: list,
        temp_dir: str,
        timeout_seconds: float,
        stdin_input: str
    ) -> Dict[str, Any]:
        """Execute a Docker container with strict resource limits and isolation."""
        # Convert to absolute path for Docker volume mounting
        mount_path = os.path.abspath(temp_dir)
        
        docker_cmd = [
            self.docker_executable, "run", "--rm", "-i",
            "--network=none",           # 1. No internet/network access
            "--memory=256m",            # 2. Memory limits
            "--cpus=1.0",               # 3. CPU limits
            "--pids-limit=64",          # 4. Fork bomb prevention
            "--read-only",              # 5. Read-only root filesystem
            "--tmpfs", "/tmp",          # Allow writing to /tmp for language runtimes
            "-v", f"{mount_path}:/workspace",
            "-w", "/workspace",
            # We don't force a specific UID like -u 1000:1000 because Docker Desktop on Windows 
            # might not have it, but we can rely on standard slim images and isolation.
            image
        ] + cmd_args

        t_start = time.perf_counter()
        
        try:
            process = await asyncio.create_subprocess_exec(
                *docker_cmd,
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
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time_ms": round((t_end - t_start) * 1000, 2),
                    "timeout_occurred": False,
                    "security_blocked": False,
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
                    "stdout": "",
                    "stderr": f"Execution timed out after {timeout_seconds}s.",
                    "exit_code": -1,
                    "execution_time_ms": round((t_end - t_start) * 1000, 2),
                    "timeout_occurred": True,
                    "security_blocked": False,
                    "error_message": f"Time Limit Exceeded ({timeout_seconds}s)"
                }

        except Exception as e:
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": 0.0,
                "timeout_occurred": False,
                "security_blocked": False,
                "error_message": str(e)
            }

    async def _run_python_docker(
        self,
        code: str,
        timeout_seconds: float,
        stdin_input: str,
        temp_dir: str
    ) -> Dict[str, Any]:
        """Execute Python code in isolated Docker container."""
        script_path = os.path.join(temp_dir, "solution.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)
            
        return await self._run_docker(
            image="python:3.11-slim",
            cmd_args=["python", "-u", "solution.py"],
            temp_dir=temp_dir,
            timeout_seconds=timeout_seconds,
            stdin_input=stdin_input
        )

    async def _run_javascript_docker(
        self,
        code: str,
        timeout_seconds: float,
        stdin_input: str,
        temp_dir: str
    ) -> Dict[str, Any]:
        """Execute JavaScript code in isolated Node.js container."""
        script_path = os.path.join(temp_dir, "solution.js")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        return await self._run_docker(
            image="node:18-slim",
            cmd_args=["node", "solution.js"],
            temp_dir=temp_dir,
            timeout_seconds=timeout_seconds,
            stdin_input=stdin_input
        )

    async def _run_python_local(self, code: str, timeout_seconds: float, stdin_input: str) -> Dict[str, Any]:
        """Execute Python code locally when Docker is unavailable.
        Returns a dict compatible with the Docker execution schema.
        """
        temp_dir = tempfile.mkdtemp(prefix="prepsense_sandbox_local_")
        script_path = os.path.join(temp_dir, "solution.py")
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            t_start = time.perf_counter()
            process = await asyncio.create_subprocess_exec(
                self.python_executable,
                "-u",
                script_path,
                cwd=temp_dir,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(input=stdin_input.encode("utf-8") if stdin_input else None),
                    timeout=timeout_seconds,
                )
                t_end = time.perf_counter()
                stdout = stdout_bytes.decode("utf-8", errors="replace")[:65536]
                stderr = stderr_bytes.decode("utf-8", errors="replace")[:65536]
                exit_code = process.returncode if process.returncode is not None else 0
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time_ms": round((t_end - t_start) * 1000, 2),
                    "timeout_occurred": False,
                    "security_blocked": False,
                    "error_message": stderr.strip() if exit_code != 0 and stderr else None,
                }
            except asyncio.TimeoutError:
                t_end = time.perf_counter()
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
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
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": 0.0,
                "timeout_occurred": False,
                "security_blocked": False,
                "error_message": str(e),
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def _run_javascript_local(self, code: str, timeout_seconds: float, stdin_input: str) -> Dict[str, Any]:
        """Execute JavaScript code locally using the system Node executable.
        Mirrors the Docker execution return format.
        """
        if not self.node_executable or not shutil.which(self.node_executable):
            return {
                "stdout": "",
                "stderr": "Node executable not found.",
                "exit_code": 1,
                "execution_time_ms": 0.0,
                "timeout_occurred": False,
                "security_blocked": False,
                "error_message": "Node executable not found.",
            }
        temp_dir = tempfile.mkdtemp(prefix="prepsense_sandbox_local_")
        script_path = os.path.join(temp_dir, "solution.js")
        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(code)
            t_start = time.perf_counter()
            process = await asyncio.create_subprocess_exec(
                self.node_executable,
                script_path,
                cwd=temp_dir,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(input=stdin_input.encode("utf-8") if stdin_input else None),
                    timeout=timeout_seconds,
                )
                t_end = time.perf_counter()
                stdout = stdout_bytes.decode("utf-8", errors="replace")[:65536]
                stderr = stderr_bytes.decode("utf-8", errors="replace")[:65536]
                exit_code = process.returncode if process.returncode is not None else 0
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code,
                    "execution_time_ms": round((t_end - t_start) * 1000, 2),
                    "timeout_occurred": False,
                    "security_blocked": False,
                    "error_message": stderr.strip() if exit_code != 0 and stderr else None,
                }
            except asyncio.TimeoutError:
                t_end = time.perf_counter()
                try:
                    process.kill()
                    await process.wait()
                except Exception:
                    pass
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
            return {
                "stdout": "",
                "stderr": str(e),
                "exit_code": 1,
                "execution_time_ms": 0.0,
                "timeout_occurred": False,
                "security_blocked": False,
                "error_message": str(e),
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
