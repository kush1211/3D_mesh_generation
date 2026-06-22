"""Critique node: render the mesh headlessly and ask Gemini if it matches.

Sets `feedback` when the render does not match, so the next generate attempt
gets the visual critique.
"""
from __future__ import annotations

import base64

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from .. import config
from ..llm.models import build_chat_model
from ..llm.prompts import CRITIQUE_PROMPT, CRITIQUE_SYSTEM
from ..render import PRIMARY_VIEW_INDEX, render_mesh_views, view_labels


class Critique(BaseModel):
    matches: bool = Field(
        description=(
            "True ONLY if the reconstructed mesh plausibly matches the product's "
            "overall shape, parts, proportions, AND orientation. If anything is "
            "clearly wrong, set this to False."
        )
    )
    shape: str = Field(
        description=(
            "Plain-language assessment of the overall silhouette and proportions "
            "versus the product: is the body the right form, and is it too tall, "
            "short, wide, or narrow? Describe what you see."
        )
    )
    parts: str = Field(
        description=(
            "Plain-language assessment of the structural parts: which expected "
            "parts are present, missing, or extra, and whether parts that should "
            "be joined look properly connected or instead detached, floating, or "
            "separated by a gap (e.g. a mug handle that does not meet the body)."
        )
    )
    orientation: str = Field(
        description=(
            "Plain-language assessment of the product's orientation: is it the "
            "right way up (standing upright, not lying on its side or upside "
            "down), is it tilted, and do asymmetric features such as a handle, "
            "spout, or opening face the correct direction?"
        )
    )
    suggested_changes: str = Field(
        default="",
        description=(
            "Concrete, plain-language description of what should change about the "
            "shape, size, placement, or orientation to better match the product. "
            "Describe WHAT to change — never name any code, library, function, or "
            "technical operation."
        ),
    )


def _mesh_metrics_text(state: dict) -> str:
    validation = state.get("validation") or {}
    execution = state.get("execution") or {}
    lines: list[str] = ["## Mesh metrics"]

    if validation:
        lines.append(f"- euler_number: {validation.get('euler_number')}")
        lines.append(f"- extents (m): {validation.get('extents')}")
        lines.append(f"- watertight: {validation.get('is_watertight')}")
        lines.append(f"- dims_ok: {validation.get('dims_ok')}")
        lines.append(f"- volume (m³): {validation.get('volume')}")

    glb_path = execution.get("glb_path")
    if glb_path:
        try:
            import trimesh

            mesh = trimesh.load(glb_path, force="mesh")
            components = mesh.split(only_watertight=False)
            lines.append(f"- connected_components: {len(components)}")
        except Exception:  # noqa: BLE001
            pass

    dims = state.get("dimensions")
    if dims:
        lines.append(f"- expected_dimensions (m): {dims}")

    return "\n".join(lines)


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
            "render_paths": None,
            "critique": {"matches": False, "reasons": msg, "suggested_fixes": ""},
            "feedback": msg,
        }

    labels = view_labels()
    content: list[dict] = [
        {"type": "text", "text": CRITIQUE_PROMPT},
        {"type": "text", "text": _mesh_metrics_text(state)},
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
    print(f"[critique] matches={c['matches']}: {c['shape'][:100]}")
    feedback = None
    if not c["matches"]:
        feedback = (
            "Visual critique — the mesh does NOT match the product. Problems:\n"
            f"- Shape & proportions: {c['shape']}\n"
            f"- Parts & structure: {c['parts']}\n"
            f"- Orientation: {c['orientation']}\n"
            f"- What to change: {c['suggested_changes']}"
        )
    primary_path = render_paths[PRIMARY_VIEW_INDEX]
    return {
        "render_path": primary_path,
        "render_paths": render_paths,
        "critique": c,
        "feedback": feedback,
    }
