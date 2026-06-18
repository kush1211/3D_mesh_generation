"""Executor interface — the single seam between agent logic and code execution."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path


@dataclass
class ExecutionResult:
    returncode: int
    stdout: str
    stderr: str
    glb_path: str | None
    timed_out: bool = False

    @property
    def ok(self) -> bool:
        return self.returncode == 0 and self.glb_path is not None and not self.timed_out


class Executor(ABC):
    """Runs generated geometry code and reports the result.

    Implementations must be pure w.r.t. agent state: given source code and a
    working directory, run it and return an ExecutionResult. No knowledge of
    plans, prompts, or the graph.
    """

    @abstractmethod
    def run(
        self,
        code: str,
        workdir: Path,
        expected_output: Path,
        timeout: int = 120,
    ) -> ExecutionResult:
        ...
