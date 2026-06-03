"""住宿与餐饮节点（NL 解析 + 对话式确认）"""

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
from app.schemas.travel import VALID_ACCOMMODATION, VALID_FOOD
from app.settings import settings

ACCOMMODATION_LABELS = {
    "star_hotel": "星级酒店",
    "economy_hotel": "经济酒店",
    "hostel": "特色民宿",
    "youth_hostel": "青年旅社",
}
FOOD_LABELS = {
    "specialty": "特色美食",
    "chain": "连锁快餐",
    "local": "本地小吃",
}

_STAY_INSTRUCTION = (
    "请询问用户住宿与餐饮偏好，给出 star_hotel / economy_hotel / hostel / youth_hostel "
    "以及 specialty / chain / local 的口语化说明，邀请用户选择。"
)


async def plan_stay_and_food(state: TravelState) -> dict:
    ctx = prepare_step_context("plan_stay_and_food", state)
    if not ctx.ready:
        return {
            "current_step": "plan_transport",
            "messages": [
                AIMessage(
                    content=f"请先完成交通方式选择（缺少：{', '.join(ctx.missing)}）。"
                )
            ],
        }

    messages = state.get("messages") or []
    extracted = await extract_planning_selections(messages)
    accommodations = list(state.get("selected_accommodation_types") or [])
    if not accommodations and extracted.selected_accommodation_types:
        accommodations = list(extracted.selected_accommodation_types)
    foods = list(state.get("selected_food_types") or [])
    if not foods and extracted.selected_food_types:
        foods = list(extracted.selected_food_types)

    if accommodations and not all(item in VALID_ACCOMMODATION for item in accommodations):
        return {
            "current_step": "plan_stay_and_food",
            "messages": [
                AIMessage(content=f"住宿类型无效，可选：{', '.join(VALID_ACCOMMODATION)}")
            ],
        }

    if foods and not all(item in VALID_FOOD for item in foods):
        return {
            "current_step": "plan_stay_and_food",
            "messages": [
                AIMessage(content=f"餐饮类型无效，可选：{', '.join(VALID_FOOD)}")
            ],
        }

    if accommodations and foods:
        acc_text = "、".join(ACCOMMODATION_LABELS[a] for a in accommodations)
        food_text = "、".join(FOOD_LABELS[f] for f in foods)
        return {
            "current_step": "plan_activities",
            "selected_accommodation_types": accommodations,
            "selected_food_types": foods,
            "messages": [
                AIMessage(content=f"住宿：{acc_text}；餐饮：{food_text}。接下来确认活动偏好。")
            ],
        }

    reply: str
    if settings.mimo_api_key and ctx.ready:
        try:
            reply = await invoke_step_llm(
                "plan_stay_and_food",
                state,
                instruction=build_step_instruction(
                    "plan_stay_and_food", state, _STAY_INSTRUCTION
                ),
                ctx=ctx,
            )
        except Exception as exc:
            logger.exception("住宿餐饮 LLM 调用失败")
            reply = (
                f"请告诉我住宿偏好（star_hotel/economy_hotel/hostel/youth_hostel）"
                f"和餐饮偏好（specialty/chain/local）。({exc})"
            )
    else:
        missing_part = "住宿" if not accommodations else "餐饮"
        reply = (
            f"请告诉我{missing_part}偏好。"
            "住宿：星级酒店/经济酒店/民宿/青年旅社；餐饮：特色美食/连锁/本地小吃。"
        )

    update: dict = {
        "current_step": "plan_stay_and_food",
        "messages": [AIMessage(content=reply)],
    }
    if accommodations:
        update["selected_accommodation_types"] = accommodations
    if foods:
        update["selected_food_types"] = foods
    return update
