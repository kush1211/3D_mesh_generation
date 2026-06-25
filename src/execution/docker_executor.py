"""Docker executor: runs generated geometry code in a hardened ephemeral container."""
from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from .. import config
from .base import ExecutionResult, Executor


class DockerExecutor(Executor):
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

        container_name = f"mesh-exec-{uuid.uuid4().hex[:12]}"
        cmd = [
            "docker",
            "run",
            "--name",
            container_name,
            "--network",
            "none",
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            f"--memory={config.DOCKER_EXEC_MEMORY}",
            f"--cpus={config.DOCKER_EXEC_CPUS}",
            f"--pids-limit={config.DOCKER_EXEC_PIDS_LIMIT}",
            "--user",
            f"{os.getuid()}:{os.getgid()}",
            "-v",
            f"{workdir.resolve()}:/work:rw",
            "-w",
            "/work",
            config.DOCKER_EXEC_IMAGE,
            "python",
            "script.py",
        ]

        proc: subprocess.CompletedProcess[str] | None = None
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired as exc:
            _remove_container(container_name)
            return ExecutionResult(
                returncode=-1,
                stdout=exc.stdout or "",
                stderr=(exc.stderr or "") + f"\n[execution timed out after {timeout}s]",
                glb_path=None,
                timed_out=True,
            )
        finally:
            _remove_container(container_name)

        assert proc is not None
        glb = str(expected_output) if expected_output.exists() else None
        return ExecutionResult(
            returncode=proc.returncode,
            stdout=proc.stdout,
            stderr=proc.stderr,
            glb_path=glb,
        )


def _remove_container(name: str) -> None:
    subprocess.run(
        ["docker", "rm", "-f", name],
        capture_output=True,
        text=True,
        timeout=30,
    )
