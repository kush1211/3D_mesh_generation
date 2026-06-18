"""Generate node: Gemini (with Context7 MCP tools) writes a trimesh script.

In real mode this is a small tool-calling ReAct agent: the model can call
Context7's resolve-library-id / query-docs to fetch live trimesh API docs
before/while emitting code. The iteration counter is incremented here.
"""
from __future__ import annotations

import re

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from .. import config
from ..llm.mcp import build_context7_tools
from ..llm.models import build_chat_model
from ..llm.prompts import GENERATE_SYSTEM, build_generate_prompt
from .stubs import STUB_CODE

_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def _extract_code(text: str) -> str:
    """Pull python out of a fenced block if present, else return as-is."""
    if not isinstance(text, str):
        # ReAct content can be a list of content blocks.
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in text
        )
    matches = _FENCE.findall(text)
    if matches:
        return max(matches, key=len).strip()
    return text.strip()


async def generate_node(state: dict) -> dict:
    iteration = state.get("iteration", 0) + 1

    if state.get("stub"):
        print(f"[generate] (stub) iteration {iteration}: canned box script")
        return {"iteration": iteration, "code": STUB_CODE}

    tools = await build_context7_tools()
    agent = create_react_agent(build_chat_model(), tools)
    prompt = build_generate_prompt(
        state["plan"], config.load_trimesh_guide(), state.get("feedback")
    )
    print(f"[generate] iteration {iteration}: querying model (+Context7, {len(tools)} tools)")
    result = await agent.ainvoke(
        {"messages": [SystemMessage(content=GENERATE_SYSTEM), HumanMessage(content=prompt)]}
    )
    code = _extract_code(result["messages"][-1].content)
    print(f"[generate] produced {len(code)} chars of code")
    return {"iteration": iteration, "code": code}
