"""Critique node: render the mesh headlessly and ask Gemini if it matches.

Sets `feedback` when the render does not match, so the next generate attempt
gets the visual critique.
"""
from __future__ import annotations

import base64

from langchain_core.messages import HumanMessage, SystemMessage

from .. import config
from ..llm.models import build_chat_model
from ..llm.prompts import CRITIQUE_PROMPT, CRITIQUE_SYSTEM
from ..llm.schemas import Critique
from ..render import render_mesh


async def critique_node(state: dict) -> dict:
    execution = state.get("execution") or {}
    glb_path = execution.get("glb_path")
    render_path = render_mesh(glb_path, config.RENDER_PATH) if glb_path else None

    if state.get("stub"):
        print("[critique] (stub) approving render")
        return {
            "render_path": render_path,
            "critique": {"matches": True, "reasons": "stub", "suggested_fixes": ""},
        }

    if not render_path:
        msg = "Could not render the mesh for visual critique."
        print(f"[critique] {msg}")
        return {
            "render_path": None,
            "critique": {"matches": False, "reasons": msg, "suggested_fixes": ""},
            "feedback": msg,
        }

    render_b64 = base64.b64encode(open(render_path, "rb").read()).decode()
    model = build_chat_model().with_structured_output(Critique)
    messages = [
        SystemMessage(content=CRITIQUE_SYSTEM),
        HumanMessage(
            content=[
                {"type": "text", "text": CRITIQUE_PROMPT},
                {"type": "text", "text": "Image 1 (original):"},
                {"type": "image_url",
                 "image_url": {"url": f"data:{state['image_mime']};base64,{state['image_b64']}"}},
                {"type": "text", "text": "Image 2 (mesh render):"},
                {"type": "image_url",
                 "image_url": {"url": f"data:image/png;base64,{render_b64}"}},
            ]
        ),
    ]
    critique: Critique = await model.ainvoke(messages)
    c = critique.model_dump()
    print(f"[critique] matches={c['matches']}: {c['reasons'][:100]}")
    feedback = None
    if not c["matches"]:
        feedback = f"Visual critique (does not match):\n{c['reasons']}\nFixes: {c['suggested_fixes']}"
    return {"render_path": render_path, "critique": c, "feedback": feedback}
