"""Safe Python code execution for the swarm coding agent."""

import subprocess
import sys
from pathlib import Path

from langchain_core.tools import tool

# Max bytes of stdout/stderr to return
OUTPUT_LIMIT = 8000
TIMEOUT_SECONDS = 15


def _run_python(code: str) -> str:
    """Run Python code in a subprocess with timeout. No network; stdout/stderr captured."""
    if not code or not code.strip():
        return "No code provided."
    code = code.strip()
    # Remove markdown code blocks if present
    if code.startswith("```"):
        lines = code.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        code = "\n".join(lines)
    try:
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
            cwd=Path.cwd(),
        )
        out = (result.stdout or "") + (result.stderr or "")
        if len(out) > OUTPUT_LIMIT:
            out = out[:OUTPUT_LIMIT] + "\n... (output truncated)"
        return out or "(no output)"
    except subprocess.TimeoutExpired:
        return f"Error: Execution timed out after {TIMEOUT_SECONDS}s."
    except Exception as e:
        return f"Error: {e}"


@tool
def run_python(code: str) -> str:
    """
    Run Python code and return the output. Use for calculations, data processing, or when the user asks to compute something.
    Input should be a string containing valid Python code. The code runs in an isolated process with a timeout.
    """
    return _run_python(code)
