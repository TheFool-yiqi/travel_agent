"""Pytest 配置。"""

import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.fixture(autouse=True)
def isolate_step_config_mcp_cache() -> None:
    """避免 MCP 步骤工具缓存在用例间泄漏（如 test_graph_middleware 污染 test_step_config）。"""
    from app.graph.step_config import reset_step_mcp_cache

    reset_step_mcp_cache()
    yield
    reset_step_mcp_cache()


def pytest_configure(config) -> None:
    """Windows 默认 GBK 控制台无法 print LLM 响应里的 emoji，集成测试 -s 会误报失败。"""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            reconfigure = getattr(stream, "reconfigure", None)
            if reconfigure is not None:
                try:
                    reconfigure(encoding="utf-8", errors="replace")
                except (OSError, ValueError):
                    pass
