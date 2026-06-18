"""Central configuration: model name, paths, limits, and API keys.

Everything tunable lives here so nodes/graph code stays declarative.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Paths -----------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKDIR = PROJECT_ROOT / "workdir"
SCRIPT_PATH = WORKDIR / "script.py"
GLB_PATH = WORKDIR / "mesh.glb"
RENDER_PATH = WORKDIR / "render.png"
TRIMESH_GUIDE_PATH = PROJECT_ROOT / "trimesh.md"

# --- LLM / MCP -------------------------------------------------------------
# Model name confirmed via web search (live in the Gemini API, mid-2026).
MODEL_NAME = "gemini-3.1-flash-lite"
CONTEXT7_URL = "https://mcp.context7.com/mcp"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CONTEXT7_API_KEY = os.getenv("CONTEXT7_API_KEY")  # optional (higher rate limits)

# --- Loop control ----------------------------------------------------------
MAX_ITERATIONS = 4
EXEC_TIMEOUT_S = 120
# Relative tolerance when comparing rendered bbox extents to planned meters.
BBOX_REL_TOLERANCE = 0.5


def ensure_workdir() -> Path:
    """Create the runtime workdir if missing and return it."""
    WORKDIR.mkdir(parents=True, exist_ok=True)
    return WORKDIR


def load_trimesh_guide() -> str:
    """Return the authoritative trimesh.md guidance to inject into prompts."""
    try:
        return TRIMESH_GUIDE_PATH.read_text(encoding="utf-8")
    except OSError:
        return ""
