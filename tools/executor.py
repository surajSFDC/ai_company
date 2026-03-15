"""Code execution for agents."""
import subprocess
import tempfile
import os
from typing import Dict, Any


class CodeExecutor:
    """Safely execute code in a sandboxed environment."""

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def execute_python(self, code: str, stdin: str = "") -> Dict[str, Any]:
        """Execute Python code and return output."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            result = subprocess.run(
                ["python", temp_file],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                input=stdin,
            )

            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "Execution timed out",
                "returncode": -1,
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1,
            }
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)

    def execute_tests(self, test_code: str, code_to_test: str) -> Dict[str, Any]:
        """Execute tests for the given code."""
        full_code = f"{code_to_test}\n\n{test_code}"
        return self.execute_python(full_code)

