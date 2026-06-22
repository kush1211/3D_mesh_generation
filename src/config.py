"""Central configuration: model name, paths, limits, and API keys.

Everything tunable lives here so nodes/graph code stays declarative.
"""
from __future__ import annotations

import functools
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

# --- LLM / MCP -------------------------------------------------------------
# Model name confirmed via web search (live in the Gemini API, mid-2026).
MODEL_NAME = "gemini-3.5-flash"
CONTEXT7_URL = "https://mcp.context7.com/mcp"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CONTEXT7_API_KEY = os.getenv("CONTEXT7_API_KEY")  # optional (higher rate limits)

# --- Loop control ----------------------------------------------------------
MAX_ITERATIONS = 4
EXEC_TIMEOUT_S = 120
# Relative tolerance when comparing rendered bbox extents to planned meters.
BBOX_REL_TOLERANCE = 0.5
# Pixel size for each critique render (five views written as render_0.png …).
CRITIQUE_RENDER_SIZE = 512


def ensure_workdir() -> Path:
    """Create the runtime workdir if missing and return it."""
    WORKDIR.mkdir(parents=True, exist_ok=True)
    return WORKDIR


TRIMESH_GUIDE_PATH = PROJECT_ROOT / "trimesh.md"


@functools.lru_cache(maxsize=1)
def load_trimesh_guide() -> str:
    """The project's authoritative geometry conventions (trimesh.md), injected
    into the generate system prompt. The leading YAML frontmatter (skill
    metadata) is stripped so only the geometry guidance reaches the model."""
    text = TRIMESH_GUIDE_PATH.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            text = parts[2]
    return text.strip()
