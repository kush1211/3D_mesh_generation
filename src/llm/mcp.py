"""Connects the in-project model to the Context7 MCP server.

The generate node binds these tools so Gemini can fetch *live* trimesh API
docs (resolve-library-id / query-docs) before writing geometry code.
"""
from __future__ import annotations

from langchain_mcp_adapters.client import MultiServerMCPClient

from .. import config


def build_context7_client() -> MultiServerMCPClient:
    headers: dict[str, str] = {}
    if config.CONTEXT7_API_KEY:
        headers["CONTEXT7_API_KEY"] = config.CONTEXT7_API_KEY
    return MultiServerMCPClient(
        {
            "context7": {
                "transport": "streamable_http",
                "url": config.CONTEXT7_URL,
                "headers": headers,
            }
        }
    )


async def build_context7_tools():
    """Return Context7 MCP tools as LangChain tools (async)."""
    client = build_context7_client()
    return await client.get_tools()
