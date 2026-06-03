"""MCP 客户端管理器：统一管理多 Server 连接与 LangChain 工具加载。"""

from __future__ import annotations

import asyncio
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from loguru import logger

from app.mcp.client import (
    ALL_MANAGER_SERVERS,
    build_manager_connections,
    normalize_server_names,
)


class MCPClientManager:
    """
    MCP 客户端管理器（异步单例）。

    用于 Agent 预加载 MCP 工具（get_tools），与 registry 的 call_tool 互补：
    - Manager：批量加载 LangChain Tool 供 ReAct Agent 绑定
    - Registry：按 server + tool 名精确调用（adapter stdio 回退）
    """

    _instance: MCPClientManager | None = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self._client: MultiServerMCPClient | None = None
        self._tools: list[BaseTool] | None = None
        self._servers: list[str] = []

    @classmethod
    async def get_instance(
        cls,
        servers: list[str] | None = None,
    ) -> MCPClientManager:
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    instance = cls()
                    await instance.initialize(servers=servers)
                    cls._instance = instance
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        cls._instance = None

    async def initialize(self, servers: list[str] | None = None) -> None:
        if self._client is not None:
            logger.debug("MCP 客户端已初始化，跳过")
            return

        selected = normalize_server_names(servers or list(ALL_MANAGER_SERVERS))
        connections = build_manager_connections(selected)
        if not connections:
            logger.warning("无可用 MCP 连接配置")
            self._client = MultiServerMCPClient({})
            self._tools = []
            self._servers = []
            return

        logger.info("初始化 MCP: {}", list(connections.keys()))
        self._client = MultiServerMCPClient(connections)
        self._servers = list(connections.keys())

        try:
            self._tools = await self._client.get_tools()
            logger.info("已加载 {} 个 MCP 工具", len(self._tools))
        except Exception as exc:
            logger.warning("预加载 MCP 工具失败: {}", exc)
            self._tools = []

    async def close(self) -> None:
        self._client = None
        self._tools = None
        self._servers = []
        logger.info("MCP 客户端已关闭")

    @property
    def servers(self) -> list[str]:
        return list(self._servers)

    async def get_tools(self) -> list[BaseTool]:
        if self._client is None:
            raise RuntimeError("MCP 客户端未初始化，请先 await initialize() 或 get_instance()")

        if self._tools:
            return self._tools

        self._tools = await self._client.get_tools()
        return self._tools

    async def get_tools_by_server(self, server_name: str) -> list[BaseTool]:
        if self._client is None:
            raise RuntimeError("MCP 客户端未初始化")
        return await self._client.get_tools(server_name=server_name)


async def get_mcp_manager(servers: list[str] | None = None) -> MCPClientManager:
    """获取 MCP 客户端管理器单例。"""
    return await MCPClientManager.get_instance(servers=servers)


def reset_mcp_manager() -> None:
    """测试重置。"""
    MCPClientManager.reset_instance()
