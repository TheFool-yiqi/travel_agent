"""每日活动偏好节点（NL 解析 + 对话式确认）"""

from __future__ import annotations

from langchain_core.messages import AIMessage
from loguru import logger

from app.graph.nl_extract import extract_planning_selections
from app.graph.state import TravelState
from app.graph.step_context import (
    build_step_instruction,
    invoke_step_llm,
    prepare_step_context,
)
from app.schemas.travel import VALID_ACTIVITY
from app.settings import settings

ACTIVITY_LABELS = {
    "culture": "文化体验",
    "nature": "自然风光",
    "food_tour": "美食探店",
    "shopping": "购物市集",
    "family_fun": "亲子休闲",
}

_ACTIVITY_INSTRUCTION = (
    "请了解用户偏好的活动类型，说明 culture / nature / food_tour / shopping / family_fun "
    "的含义，邀请用户选择一种或多种。"
)


async def plan_activities(state: TravelState) -> dict:
    ctx = prepare_step_context("plan_activities", state)
    if not ctx.ready:
        return {
            "current_step": "plan_stay_and_food",
            "messages": [
                AIMessage(
                    content=f"请先完成住宿与餐饮选择（缺少：{', '.join(ctx.missing)}）。"
                )
            ],
        }

    messages = state.get("messages") or []
    extracted = await extract_planning_selections(messages)
    activities = list(state.get("selected_activity_types") or [])
    if not activities and extracted.selected_activity_types:
        activities = list(extracted.selected_activity_types)

    if activities and not all(item in VALID_ACTIVITY for item in activities):
        return {
            "current_step": "plan_activities",
            "messages": [
                AIMessage(content=f"活动类型无效，可选：{', '.join(sorted(VALID_ACTIVITY))}")
            ],
        }

    if activities:
        label_text = "、".join(ACTIVITY_LABELS[a] for a in activities)
        return {
            "current_step": "build_itinerary",
            "selected_activity_types": activities,
            "messages": [
                AIMessage(content=f"活动偏好：{label_text}。开始生成完整行程。")
            ],
        }

    reply: str
    if settings.mimo_api_key and ctx.ready:
        try:
            reply = await invoke_step_llm(
                "plan_activities",
                state,
                instruction=build_step_instruction(
                    "plan_activities", state, _ACTIVITY_INSTRUCTION
                ),
                ctx=ctx,
            )
        except Exception as exc:
            logger.exception("活动规划 LLM 调用失败")
            reply = (
                "请告诉我您偏好的活动类型：文化、自然、美食探店、购物或亲子体验。"
                f"（{exc}）"
            )
    else:
        reply = (
            "请告诉我您偏好的活动类型：文化体验、自然风光、美食探店、购物市集或亲子休闲。"
            "可多选，例如「文化和美食」。"
        )

    return {
        "current_step": "plan_activities",
        "messages": [AIMessage(content=reply)],
    }
