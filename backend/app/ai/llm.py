"""LLM 客户端与 Agent / Graph 工厂（OpenAI 兼容模式，默认小米 MiMo）"""

import asyncio

import httpx
from langchain_openai import ChatOpenAI
from langgraph.graph.state import CompiledStateGraph
from langgraph.prebuilt import create_react_agent

from app.settings import settings

_cached_planner: CompiledStateGraph | None = None
_planner_lock = asyncio.Lock()
_mimo_sync_client: httpx.Client | None = None
_mimo_async_client: httpx.AsyncClient | None = None


def _mimo_timeout() -> httpx.Timeout:
    return httpx.Timeout(connect=15.0, read=120.0, write=30.0, pool=15.0)


def _get_mimo_http_clients() -> tuple[httpx.Client, httpx.AsyncClient]:
    """MiMo 直连客户端；默认 trust_env=False，避免系统代理导致 SSL 握手失败。"""
    global _mimo_sync_client, _mimo_async_client
    if _mimo_sync_client is None:
        _mimo_sync_client = httpx.Client(
            trust_env=settings.mimo_http_trust_env,
            timeout=_mimo_timeout(),
        )
    if _mimo_async_client is None:
        _mimo_async_client = httpx.AsyncClient(
            trust_env=settings.mimo_http_trust_env,
            timeout=_mimo_timeout(),
        )
    return _mimo_sync_client, _mimo_async_client


def get_chat_model(*, streaming: bool = False, fast: bool = False) -> ChatOpenAI:
    """获取 MiMo 对话模型。fast=True 时使用 MIMO_MODEL_FAST（简单对话）。"""
    model = settings.mimo_model_fast if fast else settings.mimo_model
    max_tokens = settings.qwen_max_tokens_fast if fast else settings.qwen_max_tokens
    http_client, http_async_client = _get_mimo_http_clients()
    return ChatOpenAI(
        model=model,
        api_key=settings.mimo_api_key,
        base_url=settings.mimo_base_url,
        temperature=settings.qwen_temperature,
        max_tokens=max_tokens,
        streaming=streaming,
        http_client=http_client,
        http_async_client=http_async_client,
    )


def get_fast_chat_model(*, streaming: bool = False) -> ChatOpenAI:
    """简单对话专用（mimo-v2.5 等 fast 模型）。"""
    return get_chat_model(streaming=streaming, fast=True)


async def create_memory_chat_agent(user_id: str):
    """
    轻量记忆对话 Agent（无分步 Graph，适用于 demo / 开放式问答）。

    与 Handoffs 参考代码中的 create_travel_agent 不同：
    正式分步规划请使用 create_travel_planner()。
    """
    from app.dependencies import get_user_memory_service

    service = await get_user_memory_service()
    memory_prompt = await service.format_memory_for_prompt(user_id)

    system_prompt = (
        "你是一个旅行规划助手。\n"
        "请结合用户的历史偏好和出行记录，进行个性化推荐。\n"
        "如果用户去过某些目的地或景点，请尽量避免重复推荐。\n"
    )
    if memory_prompt:
        system_prompt = f"{system_prompt}\n\n{memory_prompt}"

    return create_react_agent(
        get_chat_model(),
        tools=[],
        prompt=system_prompt,
    )


def get_llm(*, streaming: bool = True) -> ChatOpenAI:
    """兼容 Handoffs `get_llm()` 命名；默认 MiMo（非参考中的千问直连）。"""
    return get_chat_model(streaming=streaming)


async def create_travel_planner() -> CompiledStateGraph:
    """
    正式旅行规划 Graph（路线1：节点 + 路由 + Checkpoint）。

    等价于 Handoffs 参考代码中的 create_travel_agent + middleware + tools，
    但流程由 graph/nodes 显式编排，回退由 rollback.py 处理。
    """
    global _cached_planner
    if _cached_planner is not None:
        return _cached_planner

    async with _planner_lock:
        if _cached_planner is None:
            from app.graph.builder import build_travel_graph

            _cached_planner = await build_travel_graph()
    return _cached_planner


async def create_travel_agent() -> CompiledStateGraph:
    """
    Handoffs 兼容入口（参考 `create_travel_agent`）。

    参考实现：单 Agent + `create_step_config_middleware` + 全量 tools。
    本项目 Route 1：返回 LangGraph 编译图（`build_travel_graph`），
    步骤 prompt/tools 见 `graph/step_config`，回退见 `graph/rollback.py`。
    """
    return await create_travel_planner()
