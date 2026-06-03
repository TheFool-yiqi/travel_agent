"""
RAG 检索工具（tools 层）

供 agents/destination/explore_agent 等 ReAct Agent 绑定。
底层检索走 knowledge/rag_service → AdvancedRAGPipeline。
"""

from __future__ import annotations

from langchain_core.tools import BaseTool, tool
from loguru import logger

from app.knowledge.rag_service import search_knowledge


@tool
def search_destination_guide(query: str) -> str:
    """从旅游攻略知识库检索景点、路线、交通、游玩建议等信息。"""
    logger.info("RAG: search_destination_guide {}", query[:80])
    return search_knowledge(query)


@tool
def search_food_recommendations(query: str) -> str:
    """从知识库检索目的地美食、餐厅、小吃相关信息。"""
    logger.info("RAG: search_food_recommendations {}", query[:80])
    return search_knowledge(query, enhanced_query=f"{query} 美食 餐厅 小吃")


@tool
def search_accommodation_info(query: str) -> str:
    """从知识库检索住宿区域、酒店民宿选择建议。"""
    logger.info("RAG: search_accommodation_info {}", query[:80])
    return search_knowledge(query, enhanced_query=f"{query} 住宿 酒店 民宿")


@tool
def search_travel_tips(query: str) -> str:
    """从知识库检索旅行注意事项、季节建议、避坑指南。"""
    logger.info("RAG: search_travel_tips {}", query[:80])
    return search_knowledge(query, enhanced_query=f"{query} 注意事项 建议 提示")


def get_rag_tools() -> list[BaseTool]:
    """探索 Agent 使用的 RAG 工具列表。"""
    return [
        search_destination_guide,
        search_food_recommendations,
        search_accommodation_info,
        search_travel_tips,
    ]
