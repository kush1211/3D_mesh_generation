"""Generate node: Gemini (with Context7 MCP tools) writes a trimesh script.

The model calls Context7 tools to fetch live trimesh docs until satisfied,
then emits the final code as structured output (GeneratedCode Pydantic model).
No regex extraction — the code field is always a clean Python string.
"""
from __future__ import annotations

import base64

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from .. import config
from ..llm.mcp import build_context7_tools
from ..llm.models import build_chat_model
from ..llm.prompts import GENERATE_SYSTEM, build_generate_prompt
from ..render import view_labels


class Dimensions(BaseModel):
    width_m: float = Field(description="Width in meters (X).")
    height_m: float = Field(description="Height in meters (Z, up).")
    depth_m: float = Field(description="Depth in meters (Y).")


class GeneratedCode(BaseModel):
    code: str = Field(
        description=(
            "Complete, self-contained Python source ready to run as script.py. "
            "Raw Python only — no markdown fences, no prose, no explanations."
        ),
    )
    dimensions: Dimensions


def _previous_render_blocks(state: dict) -> tuple[list[dict], int]:
    """Image blocks for the previous attempt's renders. Empty on the first
    iteration or the validate-fail path, where no critique render describes the
    current code."""
    if state.get("iteration", 0) == 0:
        return [], 0
    render_paths = state.get("render_paths") or []
    labels = view_labels()
    blocks: list[dict] = []
    attached = 0
    for idx, path in enumerate(render_paths):
        try:
            with open(path, "rb") as f:
                render_b64 = base64.b64encode(f.read()).decode()
        except OSError:
            continue
        label = labels[idx] if idx < len(labels) else f"view {idx + 1}"
        # Image 1 is the target photo; previous-attempt renders start at Image 2.
        blocks.append(
            {"type": "text", "text": f"Image {attached + 2} (your previous attempt, {label}):"}
        )
        blocks.append(
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{render_b64}"}}
        )
        attached += 1
    return blocks, attached


async def generate_node(state: dict) -> dict:
    iteration = state.get("iteration", 0) + 1

    render_blocks, attached_renders = _previous_render_blocks(state)
    content: list[dict] = [
        {"type": "text", "text": "Image 1 (target product photo to reconstruct):"},
        {
            "type": "image_url",
            "image_url": {
                "url": f"data:{state['image_mime']};base64,{state['image_b64']}"
            },
        },
        *render_blocks,
    ]

    tools = await build_context7_tools()
    agent = create_react_agent(
        build_chat_model(),
        tools,
        response_format=GeneratedCode,
    )
    previous_code = state.get("code") if state.get("iteration", 0) > 0 else None
    prompt = build_generate_prompt(
        state.get("feedback"), previous_code, has_renders=attached_renders > 0
    )
    content.append({"type": "text", "text": prompt})

    retry_note = f", prev_code={len(previous_code)} chars" if previous_code else ""
    render_note = f", {attached_renders} prev renders" if attached_renders else ""
    print(
        f"[generate] iteration {iteration}: querying model "
        f"(+Context7, {len(tools)} tools{retry_note}{render_note})"
    )
    system_content = (
        f"{GENERATE_SYSTEM}\n\n"
        "# Geometry conventions (trimesh.md) — authoritative; follow these\n\n"
        f"{config.load_trimesh_guide()}"
    )
    result = await agent.ainvoke(
        {
            "messages": [
                SystemMessage(content=system_content),
                HumanMessage(content=content),
            ]
        }
    )
    generated = result.get("structured_response")
    if not isinstance(generated, GeneratedCode):
        raise ValueError(
            "Generate agent did not return structured_response (GeneratedCode). "
            "The model may have exhausted tool-calling steps without producing code."
        )
    print(f"[generate] produced {len(generated.code)} chars of code")
    return {
        "iteration": iteration,
        "code": generated.code,
        "dimensions": generated.dimensions.model_dump(),
        # New code → previous renders no longer describe state. Cleared so a
        # validate-fail retry doesn't feed stale renders back into generate.
        "render_paths": None,
    }
