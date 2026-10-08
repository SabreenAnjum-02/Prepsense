import os
import sys
import time
import asyncio
import logging
import tempfile
import uuid
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class SandboxedCodeRunner:
    """
    Executes untrusted candidate code securely using local Docker containers.
    This replaces the public Piston API to ensure proprietary test cases and
    candidate code never leave the local environment.
    """
    def __init__(self):
        # Map languages to Docker images and execution commands
        self.language_map = {
            "python": {"image": "python:3.11-alpine", "cmd": ["python", "/workspace/code.py"], "ext": ".py"},
            "py": {"image": "python:3.11-alpine", "cmd": ["python", "/workspace/code.py"], "ext": ".py"},
            "javascript": {"image": "node:18-alpine", "cmd": ["node", "/workspace/code.js"], "ext": ".js"},
            "js": {"image": "node:18-alpine", "cmd": ["node", "/workspace/code.js"], "ext": ".js"}
        }
        self.sandbox_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".sandbox"))
        os.makedirs(self.sandbox_dir, exist_ok=True)

    async def execute_code(
        self,
        code: str,
        language: str,
        timeout_seconds: float = 5.0,
        stdin_input: str = ""
    ) -> Dict[str, Any]:
        
        lang_lower = language.lower().strip()
        if lang_lower not in self.language_map:
            return self._build_error(f"Unsupported language for local Docker execution: {language}. Only Python/JS supported right now.")

        lang_config = self.language_map[lang_lower]
        ext = lang_config["ext"]
        
        # Create a secure temporary directory inside the local workspace (better for Docker mounts on Windows)
        run_id = str(uuid.uuid4())[:8]
        temp_dir = os.path.join(self.sandbox_dir, f"run_{run_id}")
        os.makedirs(temp_dir, exist_ok=True)
        
        code_file = os.path.join(temp_dir, f"code{ext}")
        
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)
            
        # Write stdin if provided
        stdin_file = os.path.join(temp_dir, "input.txt")
        with open(stdin_file, "w", encoding="utf-8") as f:
            f.write(stdin_input)

        # On Windows, path separators must be handled for Docker mounts, but docker CLI handles absolute Windows paths usually.
        # It's safer to ensure it's a valid host path.
        host_mount = os.path.abspath(temp_dir)
        
        # Build Docker command
        # Restrict memory, CPU, and disable network access
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "128m",
            "--cpus", "0.5",
            "-v", f"{host_mount}:/workspace:ro",
            "-w", "/workspace",
            "-i", # Keep STDIN open
            lang_config["image"]
        ] + lang_config["cmd"]

        t_start = time.perf_counter()
        
        try:
            # We redirect input.txt into the container's stdin
            with open(stdin_file, "r") as stdin_fh:
                process = await asyncio.create_subprocess_exec(
                    *docker_cmd,
                    stdin=stdin_fh,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout_seconds
                )
                
                t_end = time.perf_counter()
                
                stdout = stdout_bytes.decode('utf-8', errors='replace')
                stderr = stderr_bytes.decode('utf-8', errors='replace')
                exit_code = process.returncode
                
                return {
                    "stdout": stdout,
                    "stderr": stderr,
                    "exit_code": exit_code if exit_code is not None else 1,
                    "execution_time_ms": round((t_end - t_start) * 1000, 2),
                    "timeout_occurred": False,
                    "security_blocked": False,
                    "error_message": stderr.strip() if exit_code != 0 and stderr else None,
                }
                
            except asyncio.TimeoutError:
                t_end = time.perf_counter()
                # Kill the docker container process locally
                try:
                    process.kill()
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
            logger.error(f"Error spawning Docker process: {e}")
            return self._build_error(f"Internal execution error: {str(e)}")
        finally:
            # Cleanup temp files (best effort)
            try:
                os.remove(code_file)
                os.remove(stdin_file)
                os.rmdir(temp_dir)
            except Exception:
                pass

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
