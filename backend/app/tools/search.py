"""网页搜索（tools 层入口 → mcp/adapters）。"""

from __future__ import annotations

from langchain_core.tools import tool

from app.mcp.adapters.search_adapter import search_travel_info


def fetch_travel_search(query: str, max_results: int = 5) -> str:
    """搜索旅游相关网页信息，返回 JSON 字符串。"""
    return search_travel_info(query, max_results=max_results)


@tool
def search_web_travel_info(query: str, max_results: int = 5) -> str:
    """
    使用 Tavily 搜索旅游攻略、景点、美食、住宿等网页信息。

    Args:
        query: 搜索关键词
        max_results: 返回条数（1–10）
    """
    return fetch_travel_search(query, max_results=max_results)
