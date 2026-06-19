"""Builds and compiles the LangGraph state machine.

    START -> generate -> execute -> validate
      validate --(passed)--------> critique
      validate --(fail, retry)---> generate
      validate --(fail, capped)--> finalize
      critique --(matches)-------> finalize
      critique --(no, retry)-----> generate
      critique --(no, capped)----> finalize
    finalize -> END
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .nodes.critique import critique_node
from .nodes.execute import execute_node
from .nodes.finalize import finalize_node
from .nodes.generate import generate_node
from .nodes.routing import after_critique, after_validate
from .nodes.validate import validate_node
from .state import AgentState


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("generate", generate_node)
    g.add_node("execute", execute_node)
    g.add_node("validate", validate_node)
    g.add_node("critique", critique_node)
    g.add_node("finalize", finalize_node)

    g.add_edge(START, "generate")
    g.add_edge("generate", "execute")
    g.add_edge("execute", "validate")
    g.add_conditional_edges(
        "validate",
        after_validate,
        {"critique": "critique", "generate": "generate", "finalize": "finalize"},
    )
    g.add_conditional_edges(
        "critique",
        after_critique,
        {"generate": "generate", "finalize": "finalize"},
    )
    g.add_edge("finalize", END)

    return g.compile()
