"""MCP / provider 用 httpx 客户端工厂（可选绕过系统代理）。"""

from __future__ import annotations

import httpx

from app.settings import settings

MCP_DEFAULT_TIMEOUT = 30.0
MCP_DEFAULT_SSE_READ_TIMEOUT = 300.0


def mcp_httpx_client_factory(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    """langchain-mcp-adapters 用：MCP_HTTP_BYPASS_PROXY=true 时不走 HTTP_PROXY。"""
    kwargs: dict = {
        "follow_redirects": True,
        "trust_env": not settings.mcp_http_bypass_proxy,
    }
    if timeout is None:
        kwargs["timeout"] = httpx.Timeout(
            MCP_DEFAULT_TIMEOUT,
            read=MCP_DEFAULT_SSE_READ_TIMEOUT,
        )
    else:
        kwargs["timeout"] = timeout
    if headers is not None:
        kwargs["headers"] = headers
    if auth is not None:
        kwargs["auth"] = auth
    return httpx.AsyncClient(**kwargs)


def provider_sync_client(**kwargs) -> httpx.Client:
    """inprocess provider（QWeather / Tavily）同步客户端。"""
    return httpx.Client(
        trust_env=not settings.mcp_http_bypass_proxy,
        **kwargs,
    )


def provider_async_client(**kwargs) -> httpx.AsyncClient:
    """inprocess provider 异步客户端。"""
    return httpx.AsyncClient(
        trust_env=not settings.mcp_http_bypass_proxy,
        **kwargs,
    )
