"""Conditional-edge functions. Pure reads of state -> next-node name."""
from __future__ import annotations

from .. import config


def _can_retry(state: dict) -> bool:
    return state.get("iteration", 0) < state.get("max_iterations", config.MAX_ITERATIONS)


def after_validate(state: dict) -> str:
    """Passed -> critique; failed & retries left -> generate; else -> finalize."""
    if (state.get("validation") or {}).get("passed"):
        return "critique"
    return "generate" if _can_retry(state) else "finalize"


def after_critique(state: dict) -> str:
    """Matches -> finalize(success); no & retries left -> generate; else -> finalize."""
    if (state.get("critique") or {}).get("matches"):
        return "finalize"
    return "generate" if _can_retry(state) else "finalize"
