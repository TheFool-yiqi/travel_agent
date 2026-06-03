"""
目的地查询工具（Route 1 入口）

graph/nodes → step_context 预执行 query_destination_info
           → fetch_destination_info
           → destination_router（graph/routers）
           → explore Agent（agents）+ weather（tools）
"""

from __future__ import annotations

import asyncio

from langchain_core.tools import tool
from loguru import logger

from app.graph.routers.destination_router import run_destination_router
from app.knowledge.guide_store import read_destination_guide


def _default_query(destination: str) -> str:
    return f"推荐{destination}旅游"


def _fallback_destination_info(destination: str, exc: Exception | None = None) -> str:
    if exc is not None:
        logger.warning("目的地查询失败，回退本地攻略: {}", exc)
    guide = read_destination_guide(destination)
    if guide is not None:
        return guide
    return f"📍 未找到「{destination}」相关攻略。"


def fetch_destination_info(destination: str, query: str | None = None) -> str:
    """同步入口：供 step_context.run_step_tools 调用。"""
    text_query = query or _default_query(destination)
    try:
        return run_destination_router(destination=destination, original_query=text_query)
    except Exception as exc:
        return _fallback_destination_info(destination, exc)


async def fetch_destination_info_async(destination: str, query: str = "") -> str:
    """异步入口：供 @tool query_destination_info 调用。"""
    text_query = query or _default_query(destination)
    return await asyncio.to_thread(fetch_destination_info, destination, text_query)


@tool
async def query_destination_info(destination: str, query: str = "") -> str:
    """
    查询目的地信息（Router：探索 Agent RAG + 天气）。

    Args:
        destination: 目的地，如「西安」
        query: 可选的具体问题
    """
    return await fetch_destination_info_async(destination, query)
