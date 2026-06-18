"""Execute node: run the generated script via the pluggable Executor.

Depends ONLY on the Executor interface — swap SubprocessExecutor for a
DockerExecutor later without touching this node.
"""
from __future__ import annotations

from .. import config
from ..execution import Executor, SubprocessExecutor

# Bound here, not inside the node, so the swap point is a single line.
_EXECUTOR: Executor = SubprocessExecutor()


def execute_node(state: dict) -> dict:
    config.ensure_workdir()
    result = _EXECUTOR.run(
        code=state["code"],
        workdir=config.WORKDIR,
        expected_output=config.GLB_PATH,
        timeout=config.EXEC_TIMEOUT_S,
    )
    status = "ok" if result.ok else f"FAILED (rc={result.returncode})"
    print(f"[execute] {status}; glb={result.glb_path}")
    if not result.ok and result.stderr:
        tail = result.stderr.strip().splitlines()[-5:]
        print("[execute] stderr tail:\n  " + "\n  ".join(tail))
    return {
        "execution": {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "glb_path": result.glb_path,
            "timed_out": result.timed_out,
            "ok": result.ok,
        }
    }
