"""Generate node: Gemini (with Context7 MCP tools) writes a trimesh script.

The model calls Context7 tools to fetch live trimesh docs until satisfied,
then emits the final code as structured output (GeneratedCode Pydantic model).
No regex extraction — the code field is always a clean Python string.
"""
from __future__ import annotations

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from ..llm.mcp import build_context7_tools
from ..llm.models import build_chat_model
from ..llm.prompts import GENERATE_SYSTEM, build_generate_prompt


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


async def generate_node(state: dict) -> dict:
    iteration = state.get("iteration", 0) + 1

    image_block = {
        "type": "image_url",
        "image_url": {"url": f"data:{state['image_mime']};base64,{state['image_b64']}"},
    }

    tools = await build_context7_tools()
    agent = create_react_agent(
        build_chat_model(),
        tools,
        response_format=GeneratedCode,
    )
    previous_code = state.get("code") if state.get("iteration", 0) > 0 else None
    prompt = build_generate_prompt(state.get("feedback"), previous_code)

    retry_note = f", prev_code={len(previous_code)} chars" if previous_code else ""
    print(
        f"[generate] iteration {iteration}: querying model "
        f"(+Context7, {len(tools)} tools{retry_note})"
    )
    result = await agent.ainvoke(
        {
            "messages": [
                SystemMessage(content=GENERATE_SYSTEM),
                HumanMessage(content=[image_block, {"type": "text", "text": prompt}]),
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
    }
