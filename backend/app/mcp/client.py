"""MCP 客户端封装（langchain-mcp-adapters）。"""

from __future__ import annotations

import os
import sys
from functools import lru_cache

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.sessions import Connection

from app.mcp.http_client import mcp_httpx_client_factory
from app.settings import BACKEND_DIR, BASE_DIR, settings

# 服务名常量（manager / registry / adapter 共用）
WEATHER_SERVER = "weather"
SEARCH_SERVER = "search"
AMAP_SERVER = "amap"
TRAIN_SERVER = "train"
VARIFLIGHT_SERVER = "variflight"
AIGOHOTEL_SERVER = "aigohotel"

ALL_MANAGER_SERVERS = (
    WEATHER_SERVER,
    SEARCH_SERVER,
    AMAP_SERVER,
    TRAIN_SERVER,
    VARIFLIGHT_SERVER,
    AIGOHOTEL_SERVER,
)

# Handoffs / 参考项目服务名 → 本项目
SERVER_ALIASES: dict[str, str] = {
    "12306-mcp": TRAIN_SERVER,
    "VariFlight-Aviation": VARIFLIGHT_SERVER,
    "aigohotel-mcp": AIGOHOTEL_SERVER,
}


def normalize_server_names(servers: list[str]) -> list[str]:
    """兼容参考 Handoffs 的 MCP 服务命名。"""
    return [SERVER_ALIASES.get(name, name) for name in servers]


def _backend_pythonpath() -> dict[str, str]:
    """子进程 MCP Server 需能 import app.*"""
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    backend = str(BACKEND_DIR)
    env["PYTHONPATH"] = backend if not existing else f"{backend}{os.pathsep}{existing}"
    return env


def _stdio_connection(module: str) -> Connection:
    command = settings.mcp_python_command or sys.executable
    return {
        "transport": "stdio",
        "command": command,
        "args": ["-m", module],
        "env": _backend_pythonpath(),
        "cwd": str(BASE_DIR),
    }


def build_registry_connections() -> dict[str, Connection]:
    """
    Registry / adapter 用：仅在 MCP_*_TRANSPORT=stdio 时注册本地 Server。
    """
    connections: dict[str, Connection] = {}

    if settings.mcp_weather_transport == "stdio":
        connections[WEATHER_SERVER] = _stdio_connection("app.mcp.servers.weather_server")

    if settings.mcp_search_transport == "stdio":
        connections[SEARCH_SERVER] = _stdio_connection("app.mcp.servers.search_server")

    return connections


def build_manager_connections(
    servers: list[str] | None = None,
) -> dict[str, Connection]:
    """
    MCPClientManager 用：本地 stdio + 已配置凭证的外部 HTTP MCP。
    """
    configs: dict[str, Connection] = {
        WEATHER_SERVER: _stdio_connection("app.mcp.servers.weather_server"),
        SEARCH_SERVER: _stdio_connection("app.mcp.servers.search_server"),
    }

    if settings.amap_api_key:
        configs[AMAP_SERVER] = {
            "transport": "http",
            "url": f"https://mcp.amap.com/mcp?key={settings.amap_api_key}",
            "httpx_client_factory": mcp_httpx_client_factory,
        }

    if settings.mcp_train_url:
        configs[TRAIN_SERVER] = {
            "transport": "streamable_http",
            "url": settings.mcp_train_url.rstrip("/"),
            "httpx_client_factory": mcp_httpx_client_factory,
        }

    if settings.variflight_api_key:
        configs[VARIFLIGHT_SERVER] = {
            "transport": "streamable_http",
            "url": (
                "https://ai.variflight.com/servers/aviation/mcp/"
                f"?api_key={settings.variflight_api_key}"
            ),
            "httpx_client_factory": mcp_httpx_client_factory,
        }

    if settings.aigohotel_api_key:
        configs[AIGOHOTEL_SERVER] = {
            "transport": "streamable_http",
            "url": settings.aigohotel_base_url.rstrip("/"),
            "headers": {
                "Authorization": f"Bearer {settings.aigohotel_api_key}",
                "Content-Type": "application/json",
            },
            "httpx_client_factory": mcp_httpx_client_factory,
        }

    if servers is None:
        return configs
    return {name: cfg for name, cfg in configs.items() if name in servers}


def build_mcp_connections() -> dict[str, Connection]:
    """向后兼容：registry 使用的连接表。"""
    return build_registry_connections()


@lru_cache(maxsize=1)
def get_mcp_client() -> MultiServerMCPClient:
    return MultiServerMCPClient(build_registry_connections())


def reset_mcp_client() -> None:
    """测试或配置热更新时清缓存。"""
    get_mcp_client.cache_clear()
