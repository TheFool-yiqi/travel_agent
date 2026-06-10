"""LLM 客户端（OpenAI 兼容模式，默认小米 MiMo）"""

import httpx
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from app.settings import settings

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
