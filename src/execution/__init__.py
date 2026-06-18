"""Code-execution layer. Swap point: subprocess today, Docker later.

`execute_node` depends ONLY on `execution.base.Executor`, so a future
`DockerExecutor` drops in without touching any agent/graph/LLM code.
"""
from .base import ExecutionResult, Executor
from .subprocess_executor import SubprocessExecutor

__all__ = ["ExecutionResult", "Executor", "SubprocessExecutor"]
