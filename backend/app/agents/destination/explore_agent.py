"""
探索 Agent（agents 层）

在 destination_router 的 explore 节点内运行：
ReAct + tools/rag 中的 RAG 工具，自主决定检索策略。
"""

from __future__ import annotations

from functools import lru_cache

from langchain_core.messages import HumanMessage
from langgraph.prebuilt import create_react_agent
from loguru import logger

from app.ai.llm import get_chat_model
from app.knowledge.rag_query import rag_search
from app.settings import settings
from app.tools.rag import get_rag_tools

_EXPLORE_PROMPT = """你是目的地探索专家，通过知识库工具回答用户关于某城市的查询。

可用工具：search_destination_guide、search_food_recommendations、
search_accommodation_info、search_travel_tips。

按需调用一个或多个工具；query 中须包含目的地名称。
只引用工具返回内容，不要编造具体票价或开放时间。"""


def _extract_agent_text(result: dict) -> str:
    messages = result.get("messages") or []
    if not messages:
        return ""
    content = messages[-1].content
    return content if isinstance(content, str) else str(content)


@lru_cache(maxsize=1)
def create_explore_agent():
    agent = create_react_agent(
        get_chat_model().bind(temperature=0.7),
        tools=get_rag_tools(),
        prompt=_EXPLORE_PROMPT,
    )
    logger.debug("探索 Agent 已创建")
    return agent


def run_explore_agent(destination: str, query: str) -> str:
    """运行探索 Agent；失败或无 LLM 时回退 rag_search。"""
    fallback_body = rag_search(
        query, destination=destination, top_k=3, query_strategy="auto"
    )
    fallback = f"## {destination} 知识库检索\n\n{fallback_body}"

    if not settings.mimo_api_key:
        logger.warning("MIMO_API_KEY 未配置，探索回退 rag_search")
        return fallback

    user_message = f"目的地：{destination}\n查询：{query}"
    try:
        result = create_explore_agent().invoke(
            {"messages": [HumanMessage(content=user_message)]}
        )
        text = _extract_agent_text(result).strip()
        if not text:
            return fallback
        return f"## {destination} 旅游信息\n\n{text}"
    except Exception as exc:
        logger.warning("探索 Agent 失败，回退 rag_search: {}", exc)
        return fallback
