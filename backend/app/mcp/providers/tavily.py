"""Tavily 搜索 HTTP 实现（MCP provider 与 adapter 共用）。"""

from __future__ import annotations

import json

import httpx
from loguru import logger

from app.mcp.http_client import provider_sync_client
from app.settings import settings

TAVILY_URL = "https://api.tavily.com/search"


def fetch_travel_search_json(query: str, max_results: int | None = None) -> str:
    """
    搜索旅游相关信息，返回 JSON 字符串。

    包含 answer（摘要）与 results（标题、URL、内容片段）。
    """
    if not settings.tavily_api_key:
        return json.dumps({"error": "未配置 TAVILY_API_KEY"}, ensure_ascii=False)

    limit = max_results if max_results is not None else settings.tavily_max_results
    limit = min(max(1, limit), 10)

    payload = {
        "api_key": settings.tavily_api_key,
        "query": query,
        "search_depth": settings.tavily_search_depth,
        "max_results": limit,
        "include_answer": True,
    }

    try:
        with provider_sync_client(timeout=30.0) as client:
            response = client.post(TAVILY_URL, json=payload)
    except httpx.TimeoutException:
        return json.dumps({"error": "请求超时"}, ensure_ascii=False)
    except httpx.HTTPError as exc:
        logger.error("Tavily 请求失败: {}", exc)
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    if response.status_code != 200:
        return json.dumps(
            {"error": f"API 请求失败: {response.status_code}"},
            ensure_ascii=False,
        )

    data = response.json()
    result = {
        "query": query,
        "answer": data.get("answer"),
        "results": [
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "content": (item.get("content") or "")[:300],
            }
            for item in data.get("results", [])
        ],
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
