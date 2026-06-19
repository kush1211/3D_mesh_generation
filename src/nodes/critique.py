"""Critique node: render the mesh headlessly and ask Gemini if it matches.

Sets `feedback` when the render does not match, so the next generate attempt
gets the visual critique.
"""
from __future__ import annotations

import base64

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel

from .. import config
from ..llm.models import build_chat_model
from ..llm.prompts import CRITIQUE_PROMPT, CRITIQUE_SYSTEM
from ..render import render_mesh_views, view_labels


class Critique(BaseModel):
    matches: bool
    reasons: str
    suggested_fixes: str = ""


async def critique_node(state: dict) -> dict:
    execution = state.get("execution") or {}
    glb_path = execution.get("glb_path")
    render_paths = (
        render_mesh_views(glb_path, config.WORKDIR, config.RENDER_PATH)
        if glb_path
        else []
    )

    if not render_paths:
        msg = "Could not render the mesh for visual critique."
        print(f"[critique] {msg}")
        return {
            "render_path": None,
            "critique": {"matches": False, "reasons": msg, "suggested_fixes": ""},
            "feedback": msg,
        }

    labels = view_labels()
    content: list[dict] = [
        {"type": "text", "text": CRITIQUE_PROMPT},
        {"type": "text", "text": "Image 1 (original product photo):"},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{state['image_mime']};base64,{state['image_b64']}"
            },
        },
    ]
    for i, path in enumerate(render_paths, start=2):
        label = labels[i - 2] if i - 2 < len(labels) else f"view {i - 1}"
        with open(path, "rb") as f:
            render_b64 = base64.b64encode(f.read()).decode()
        content.append({"type": "text", "text": f"Image {i} (mesh render, {label}):"})
        content.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{render_b64}"},
            }
        )

    model = build_chat_model().with_structured_output(Critique)
    messages = [
        SystemMessage(content=CRITIQUE_SYSTEM),
        HumanMessage(content=content),
    ]
    critique: Critique = await model.ainvoke(messages)
    c = critique.model_dump()
    print(f"[critique] matches={c['matches']}: {c['reasons'][:100]}")
    feedback = None
    if not c["matches"]:
        feedback = f"Visual critique (does not match):\n{c['reasons']}\nFixes: {c['suggested_fixes']}"
    return {"render_path": render_paths[0], "critique": c, "feedback": feedback}
