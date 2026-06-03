"""目的地规划节点（对应 select_destination_tool）"""

from langchain_core.messages import AIMessage
from loguru import logger

from app.graph.nl_extract import extract_planning_selections
from app.graph.state import TravelState
from app.graph.step_context import (
    build_step_instruction,
    invoke_step_llm,
    prepare_step_context,
)

_DESTINATION_INSTRUCTION = (
    "请根据用户需求推荐 3 个目的地，说明每个目的地的特色、天气适宜度与适合理由。"
    "若上方【工具查询结果】含 Router 报告，请优先引用其中的景点与天气信息。"
    "邀请用户确认选择哪一个，确认后写入 selected_destination。"
)


async def plan_destination(state: TravelState) -> dict:
    ctx = prepare_step_context("plan_destination", state)
    if not ctx.ready:
        return {
            "current_step": "collect_requirements",
            "messages": [
                AIMessage(
                    content=f"缺少前置信息：{', '.join(ctx.missing)}，请先完成需求收集。"
                )
            ],
        }

    messages = state.get("messages") or []
    extracted = await extract_planning_selections(messages)
    selected = (
        state.get("selected_destination")
        or state.get("destination")
        or extracted.selected_destination
    )
    if selected:
        return {
            "current_step": "plan_transport",
            "selected_destination": selected,
            "destination": selected,
            "messages": [AIMessage(content=f"目的地已确认：{selected}")],
        }

    try:
        content = await invoke_step_llm(
            "plan_destination",
            state,
            instruction=build_step_instruction(
                "plan_destination", state, _DESTINATION_INSTRUCTION
            ),
            ctx=ctx,
        )
    except Exception as exc:
        logger.exception("目的地推荐 LLM 调用失败")
        requirement = state.get("user_requirement") or {}
        hint = requirement.get("destination") or "待推荐"
        content = (
            f"暂时无法连接推荐服务（{exc}）。"
            f"请直接告知想去的城市，或在下一轮传入 selected_destination（建议：{hint}）。"
        )

    return {
        "current_step": "plan_destination",
        "messages": [AIMessage(content=content)],
    }
