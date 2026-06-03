"""
FastAPI 应用入口（Route 1）

生命周期：Checkpointer → Store → MCP → step_config
路由：/api/v1/users | /sessions | /conversations | /chat
"""
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1 import api_v1_router
from app.dependencies import CheckpointerManager, get_user_memory_service
from app.lifespan import app_lifespan
from app.settings import settings
from app.utils.logging import setup_logger

setup_logger()

# 开发环境可放宽 CORS；生产请在 .env 配置具体域名
CORS_ORIGINS = (
    ["*"]
    if settings.is_development
    else [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
)

app = FastAPI(
    title="LangGraph 旅行规划系统",
    description="企业级多 Agent 旅行规划服务",
    version="1.0.0",
    debug=settings.debug,
    lifespan=app_lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "{method} {path} {status} {duration:.1f}ms",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration=duration_ms,
    )
    return response


# 等价 Handoffs:
# app.include_router(users.router, prefix="/api/v1")
# app.include_router(conversations.router, prefix="/api/v1")
# app.include_router(chat.router, prefix="/api/v1")
app.include_router(api_v1_router)


@app.get("/")
async def root():
    return {
        "status": "healthy",
        "service": "LangGraph Travel Planner",
        "version": "1.0.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}


@app.get("/api/health")
async def health_check():
    try:
        manager = await CheckpointerManager.get_instance()
        manager.get_checkpointer()
        await get_user_memory_service()

        from app.mcp.manager import MCPClientManager

        mcp = MCPClientManager._instance
        mcp_info = None
        if mcp is not None and mcp.servers:
            tools = await mcp.get_tools()
            mcp_info = {"servers": mcp.servers, "tool_count": len(tools)}

        return {
            "status": "healthy",
            "env": settings.app_env,
            "components": {
                "checkpointer": manager.backend,
                "store": "postgres",
                "llm": settings.mimo_model,
                "mcp": mcp_info,
            },
        }
    except Exception as e:
        logger.error("健康检查失败: {}", e)
        return {
            "status": "unhealthy",
            "env": settings.app_env,
            "error": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
