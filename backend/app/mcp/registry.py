"""MCP 工具注册与调用。"""

from __future__ import annotations

import asyncio
import concurrent.futures
from functools import lru_cache
from typing import Any

from loguru import logger
from mcp.types import TextContent

from app.mcp.client import get_mcp_client, reset_mcp_client


def _extract_tool_text(result: Any) -> str:
    """从 MCP call_tool 结果提取文本。"""
    if isinstance(result, str):
        return result

    content = getattr(result, "content", None)
    if content is None and isinstance(result, dict):
        content = result.get("content")

    if not content:
        return str(result)

    parts: list[str] = []
    for block in content:
        if isinstance(block, TextContent):
            parts.append(block.text)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        elif hasattr(block, "text"):
            parts.append(str(block.text))
    return "\n".join(part for part in parts if part).strip() or str(result)


def _run_async(coro: Any) -> Any:
    """在同步上下文中执行 MCP 异步调用。"""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, coro).result()


run_async = _run_async


class MCPRegistry:
    """MCP 工具注册表：按 server + tool 名调用。"""

    async def call_tool(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any] | None = None,
    ) -> str:
        client = get_mcp_client()
        if server not in client.connections:
            raise ValueError(
                f"MCP server '{server}' 未配置，"
                f"可用: {list(client.connections.keys())}"
            )

        async with client.session(server) as session:
            result = await session.call_tool(tool, arguments or {})
            text = _extract_tool_text(result)
            logger.debug("MCP {}.{} → {} chars", server, tool, len(text))
            return text

    def call_tool_sync(
        self,
        server: str,
        tool: str,
        arguments: dict[str, Any] | None = None,
    ) -> str:
        return _run_async(self.call_tool(server, tool, arguments))


@lru_cache(maxsize=1)
def get_registry() -> MCPRegistry:
    return MCPRegistry()


def reset_registry() -> None:
    get_registry.cache_clear()
    reset_mcp_client()
    from app.mcp.manager import reset_mcp_manager

    reset_mcp_manager()
