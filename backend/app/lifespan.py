"""
应用生命周期（兼容 Handoffs checkpointer_lifespan + store_lifespan + MCP 初始化）。

Route 1：Checkpointer 与 Postgres Store 共用 CheckpointerManager；
MCP 通过 MCPClientManager 预加载，step_config 在启动时刷新。
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from loguru import logger

from app.dependencies import CheckpointerManager
from app.mcp.client import build_manager_connections, normalize_server_names
from app.mcp.manager import MCPClientManager, get_mcp_manager, reset_mcp_manager

# 参考 Handoffs 默认 MCP 服务列表（别名由 client.normalize_server_names 解析）
DEFAULT_MCP_SERVER_NAMES = [
    "weather",
    "search",
    "amap",
    "12306-mcp",
    "VariFlight-Aviation",
    "aigohotel-mcp",
]


@asynccontextmanager
async def checkpointer_lifespan() -> AsyncIterator[CheckpointerManager]:
    """兼容 Handoffs：初始化 / 关闭 LangGraph Checkpointer + Store 连接池。"""
    manager = await CheckpointerManager.get_instance()
    try:
        yield manager
    finally:
        await manager.close()
        CheckpointerManager._instance = None


@asynccontextmanager
async def store_lifespan() -> AsyncIterator[None]:
    """
    兼容 Handoffs store_lifespan。

    本项目 Store 与 Checkpointer 共用 CheckpointerManager 连接池，此处为 no-op 包装。
    """
    yield


@asynccontextmanager
async def mcp_lifespan(
    servers: list[str] | None = None,
) -> AsyncIterator[MCPClientManager | None]:
    """预加载 MCP 工具（仅连接 .env 中已配置的服务）。"""
    requested = normalize_server_names(servers or DEFAULT_MCP_SERVER_NAMES)
    available = list(build_manager_connections(requested).keys())
    if not available:
        logger.warning("无可用 MCP 连接配置，跳过 MCP 预加载")
        yield None
        return

    manager = await get_mcp_manager(servers=requested)
    try:
        tools = await manager.get_tools()
        logger.info(
            "MCP 服务初始化成功 servers={} tools={}",
            manager.servers,
            len(tools),
        )
        yield manager
    finally:
        await manager.close()
        reset_mcp_manager()
        logger.info("MCP 客户端已关闭")


@asynccontextmanager
async def app_lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """FastAPI lifespan：Checkpointer → Store → MCP → step_config。"""
    import asyncio

    from app.graph.step_config import apply_step_config_from_mcp, reset_step_mcp_cache

    loop = asyncio.get_running_loop()
    logger.info("FastAPI 事件循环: {}", type(loop).__name__)
    logger.info("启动应用...")

    async with checkpointer_lifespan():
        logger.info("Checkpointer 已就绪")

        async with store_lifespan():
            logger.info("Store 已就绪")

            async with mcp_lifespan():
                await apply_step_config_from_mcp()
                logger.info("步骤配置与 MCP 工具缓存已就绪")

                from app.ai.llm import create_travel_planner

                await create_travel_planner()
                logger.info("旅行规划 Graph 已预编译")

                try:
                    yield
                finally:
                    reset_step_mcp_cache()

    logger.info("应用已关闭")
