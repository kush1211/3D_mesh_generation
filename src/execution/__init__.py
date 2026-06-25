"""Code-execution layer. Swap point: DockerExecutor (hardened container).

`execute_node` depends ONLY on `execution.base.Executor`, so a different
implementation drops in without touching any agent/graph/LLM code.
"""
from .base import ExecutionResult, Executor
from .docker_executor import DockerExecutor
from .subprocess_executor import SubprocessExecutor

__all__ = ["ExecutionResult", "Executor", "DockerExecutor", "SubprocessExecutor"]
