"""Local subprocess executor: writes code to a temp file and runs it.

Prototype-only (trusted machine). Runs with the current interpreter so the
generated trimesh code shares this venv's dependencies.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .base import ExecutionResult, Executor


class SubprocessExecutor(Executor):
    def __init__(self, python_executable: str | None = None) -> None:
        self.python = python_executable or sys.executable

    def run(
        self,
        code: str,
        workdir: Path,
        expected_output: Path,
        timeout: int = 120,
    ) -> ExecutionResult:
        workdir = Path(workdir)
        workdir.mkdir(parents=True, exist_ok=True)
        script = workdir / "script.py"
        script.write_text(code, encoding="utf-8")

        # Clear any stale output so we never mistake a previous run's mesh.
        if expected_output.exists():
            expected_output.unlink()

        try:
            proc = subprocess.run(
                [self.python, str(script)],
                cwd=str(workdir),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                returncode=-1,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + f"\n[execution timed out after {timeout}s]",
                glb_path=None,
                timed_out=True,
            )

        glb = str(expected_output) if expected_output.exists() else None
        return ExecutionResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            glb_path=glb,
        )
