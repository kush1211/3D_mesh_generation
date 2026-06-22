"""The shared graph state passed between LangGraph nodes."""
from __future__ import annotations

from typing import Any, Optional, TypedDict


class AgentState(TypedDict, total=False):
    # Input
    image_path: str
    image_b64: str
    image_mime: str

    # Per-node products
    dimensions: Optional[dict[str, Any]]
    code: Optional[str]
    execution: Optional[dict[str, Any]]
    validation: Optional[dict[str, Any]]
    critique: Optional[dict[str, Any]]
    render_path: Optional[str]
    render_paths: Optional[list[str]]  # all critique view renders of the current mesh

    # Loop control
    iteration: int
    max_iterations: int
    feedback: Optional[str]
    status: str  # "running" | "success" | "failed"
