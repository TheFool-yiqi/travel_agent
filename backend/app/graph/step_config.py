"""Handoffs 步骤配置（Route 1：prompt 在 ai/prompts/，tools 由节点预执行）。"""

from __future__ import annotations

import copy
from typing import Any

from langchain_core.tools.base import BaseTool
from loguru import logger

from app.graph.steps import PLANNING_STEPS, STEP_LABELS, normalize_step
from app.graph.state import TravelState
from app.tools.datetime_tools import get_current_date
from app.tools.router_query import query_destination_info
from app.tools.search import search_web_travel_info
from app.tools.transport_query import query_transport_options

# 参考 Handoffs 8 步 → 本项目 6 步（见 steps.STEP_ALIASES）
_BASE_STEP_CONFIG: dict[str, dict[str, Any]] = {
    "collect_requirements": {
        "label": "需求收集",
        "requires": [],
        "rollback_targets": [],
        "tools": [get_current_date],
    },
    "plan_destination": {
        "label": "目的地推荐",
        "requires": ["user_requirement"],
        "rollback_targets": ["collect_requirements"],
        "tools": [query_destination_info, search_web_travel_info],
    },
    "plan_transport": {
        "label": "交通规划",
        "requires": ["user_requirement", "selected_destination"],
        "rollback_targets": ["plan_destination", "collect_requirements"],
        "tools": [query_transport_options],
    },
    "plan_stay_and_food": {
        "label": "住宿与餐饮",
        "requires": ["user_requirement", "selected_destination", "selected_transport"],
        "rollback_targets": [
            "plan_transport",
            "plan_destination",
            "collect_requirements",
        ],
        "tools": [],
    },
    "plan_activities": {
        "label": "活动规划",
        "requires": [
            "user_requirement",
            "selected_destination",
            "selected_transport",
            "selected_accommodation_types",
            "selected_food_types",
        ],
        "rollback_targets": [
            "plan_stay_and_food",
            "plan_transport",
            "plan_destination",
            "collect_requirements",
        ],
        "tools": [],
    },
    "build_itinerary": {
        "label": "行程与预算",
        "requires": [
            "user_requirement",
            "selected_destination",
            "selected_transport",
            "selected_accommodation_types",
            "selected_food_types",
            "selected_activity_types",
        ],
        "rollback_targets": [
            "plan_activities",
            "plan_stay_and_food",
            "plan_transport",
            "plan_destination",
            "collect_requirements",
        ],
        "tools": [query_destination_info, search_web_travel_info],
    },
    "approval_node": {
        "label": "行程确认",
        "requires": ["user_requirement", "itinerary", "budget"],
        "rollback_targets": [
            "build_itinerary",
            "plan_activities",
            "plan_stay_and_food",
            "plan_transport",
            "plan_destination",
            "collect_requirements",
        ],
        "tools": [],
    },
    "final_response": {
        "label": "订单生成",
        "requires": ["user_requirement", "itinerary", "budget"],
        "rollback_targets": [
            "build_itinerary",
            "plan_stay_and_food",
            "plan_transport",
            "plan_destination",
            "collect_requirements",
        ],
        "tools": [],
    },
}

_mcp_tools_cache: dict[str, list[BaseTool]] = {
    "hotel": [],
    "search": [],
    "date": [],
}
_mcp_tools_loaded: bool = False


def _merge_tools(*groups: list[BaseTool]) -> list[BaseTool]:
    """按 tool.name 去重，保留先出现的。"""
    merged: list[BaseTool] = []
    seen: set[str] = set()
    for group in groups:
        for tool in group:
            name = tool.name
            if name in seen:
                continue
            seen.add(name)
            merged.append(tool)
    return merged


def _build_merged_config() -> dict[str, dict]:
    config = copy.deepcopy(_BASE_STEP_CONFIG)

    date_tools = _mcp_tools_cache["date"] or [get_current_date]
    search_tools = _mcp_tools_cache["search"] or [search_web_travel_info]
    hotel_tools = _mcp_tools_cache["hotel"]

    config["collect_requirements"]["tools"] = _merge_tools(date_tools)
    config["plan_destination"]["tools"] = _merge_tools(
        [query_destination_info],
        search_tools,
    )
    config["plan_stay_and_food"]["tools"] = _merge_tools(hotel_tools)

    return config


async def refresh_step_mcp_tools() -> None:
    """异步加载 MCP 工具并写入缓存（graph 启动时调用）。"""
    global _mcp_tools_loaded
    from app.tools.mcp_tools import get_date_tools, get_hotel_tools, get_search_tools

    try:
        hotel_tools = await get_hotel_tools()
        search_tools = await get_search_tools()
        date_tools = await get_date_tools()
    except Exception as exc:
        logger.warning("MCP 工具加载失败: {}", exc)
        hotel_tools, search_tools, date_tools = [], [], [get_current_date]

    _mcp_tools_cache["hotel"] = hotel_tools
    _mcp_tools_cache["search"] = search_tools if search_tools else [search_web_travel_info]
    _mcp_tools_cache["date"] = date_tools if date_tools else [get_current_date]
    _mcp_tools_loaded = True

    logger.info(
        "步骤 MCP 工具: hotel={} search={} date={}",
        [t.name for t in _mcp_tools_cache["hotel"]],
        [t.name for t in _mcp_tools_cache["search"]],
        [t.name for t in _mcp_tools_cache["date"]],
    )


async def get_step_config() -> dict[str, dict]:
    """
    异步获取步骤配置（参考 Handoffs get_step_config）。

    首次调用会加载 MCP 工具；之后使用缓存。
    """
    if not _mcp_tools_loaded:
        await refresh_step_mcp_tools()
    return _build_merged_config()


def get_step_config_sync() -> dict[str, dict]:
    """同步获取步骤配置（单元测试 / 脚本；不触发 MCP 加载）。"""
    return _build_merged_config()


# 向后兼容：模块 import 时即含 inprocess 工具
STEP_CONFIG: dict[str, dict] = _build_merged_config()


def get_step_meta(step: str) -> dict:
    step = normalize_step(step)
    config = STEP_CONFIG.get(step) or _BASE_STEP_CONFIG.get(step)
    if config is None:
        raise KeyError(f"未知步骤: {step}")
    return config


def get_step_tools(step: str) -> list[BaseTool]:
    """获取步骤关联工具（Route 1：供 run_step_tools 预执行）。"""
    return list(get_step_meta(step).get("tools") or [])


def assert_step_requirements(step: str, state: TravelState) -> list[str]:
    step = normalize_step(step)
    config = get_step_meta(step)
    missing: list[str] = []
    for field in config["requires"]:
        value = state.get(field)
        if value is None:
            missing.append(field)
        elif isinstance(value, (list, dict)) and len(value) == 0:
            missing.append(field)
    return missing


def list_planning_steps() -> list[dict]:
    return [
        {
            "step": step,
            "label": STEP_CONFIG[step]["label"],
            "order": index + 1,
        }
        for index, step in enumerate(PLANNING_STEPS)
    ]


async def apply_step_config_from_mcp() -> dict[str, dict]:
    """加载 MCP 并刷新模块级 STEP_CONFIG（graph 启动用）。"""
    global STEP_CONFIG
    await refresh_step_mcp_tools()
    STEP_CONFIG = _build_merged_config()
    return STEP_CONFIG


def reset_step_mcp_cache() -> None:
    """应用关闭时清 MCP 步骤工具缓存。"""
    global STEP_CONFIG, _mcp_tools_loaded
    _mcp_tools_cache["hotel"] = []
    _mcp_tools_cache["search"] = []
    _mcp_tools_cache["date"] = []
    _mcp_tools_loaded = False
    STEP_CONFIG = _build_merged_config()