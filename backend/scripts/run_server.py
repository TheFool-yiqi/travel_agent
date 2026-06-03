"""
启动 FastAPI（Windows 强制 SelectorEventLoop，兼容 psycopg / LangGraph）。

用法（项目根目录）::

    uv run python backend/scripts/run_server.py

开发热重载（非 Windows 或接受 Windows 下 Proactor 风险）::

    uv run uvicorn app.main:app --reload --app-dir backend
"""
from __future__ import annotations

import asyncio
import sys

# 必须在导入 app / uvicorn 应用模块之前设置（Windows）
if sys.platform == "win32":
    import selectors

    _selector = selectors.SelectSelector()
    _loop = asyncio.SelectorEventLoop(_selector)
    asyncio.set_event_loop(_loop)
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import uvicorn

from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()


def main() -> None:
    host = settings.app_host
    port = settings.app_port

    if sys.platform == "win32":
        # reload=True 会 spawn 子进程并重建 ProactorEventLoop，与手动 loop 冲突
        config = uvicorn.Config(
            "app.main:app",
            host=host,
            port=port,
            reload=False,
            loop="none",
            log_level="debug" if settings.debug else "info",
        )
        server = uvicorn.Server(config)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(server.serve())
        return

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )


if __name__ == "__main__":
    main()
