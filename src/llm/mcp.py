"""Connects the in-project model to the Context7 MCP server.

The generate node binds these tools so Gemini can fetch *live* trimesh API
docs (resolve-library-id / query-docs) before writing geometry code.
"""
from __future__ import annotations

import asyncio

from langchain_mcp_adapters.client import MultiServerMCPClient

from .. import config

_tools_cache: list | None = None
_tools_lock = asyncio.Lock()


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
    """Return Context7 MCP tools as LangChain tools (cached per process)."""
    global _tools_cache
    if _tools_cache is not None:
        return _tools_cache

    async with _tools_lock:
        if _tools_cache is None:
            client = build_context7_client()
            _tools_cache = await client.get_tools()
    return _tools_cache
