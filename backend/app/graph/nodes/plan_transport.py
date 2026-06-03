"""交通规划节点（对应 select_transport_tool）"""

from langchain_core.messages import AIMessage
from loguru import logger

from app.graph.nl_extract import extract_planning_selections
from app.graph.state import TravelState
from app.graph.step_context import (
    build_step_instruction,
    invoke_step_llm,
    prepare_step_context,
    run_step_tools,
)
from app.graph.validators.transport import append_grounding_notice, validate_transport_reply
from app.schemas.travel import VALID_TRANSPORT

TRANSPORT_LABELS = {
    "flight": "航班",
    "train": "高铁",
    "driving": "自驾",
}

_TRANSPORT_INSTRUCTION = (
    "请先简要说明 flight / train / driving 三种方式的特点，询问用户偏好。"
    "若上方【工具查询结果】含协调器返回的方案，请直接展示并对比。"
    "禁止编造具体航班号/车次号/精确票价/时刻表；只能引用【工具查询结果】中的信息，"
    "无查询结果时说明「以下为参考，请以预订页面为准」。"
    "邀请用户确认选择，确认后写入 selected_transport。"
    "回复末尾请明确写出可选值：flight、train、driving。"
)


async def plan_transport(state: TravelState) -> dict:
    ctx = prepare_step_context("plan_transport", state)
    if not ctx.ready:
        return {
            "current_step": "plan_destination",
            "messages": [
                AIMessage(
                    content=f"缺少前置信息：{', '.join(ctx.missing)}，请先完成目的地选择。"
                )
            ],
        }

    messages = state.get("messages") or []
    extracted = await extract_planning_selections(messages)
    transport = state.get("selected_transport") or extracted.selected_transport
    if transport:
        if transport not in VALID_TRANSPORT:
            return {
                "current_step": "plan_transport",
                "messages": [
                    AIMessage(content="交通方式无效，请选择：flight、train 或 driving。")
                ],
            }
        return {
            "current_step": "plan_stay_and_food",
            "selected_transport": transport,
            "messages": [
                AIMessage(content=f"交通方式已确认：{TRANSPORT_LABELS[transport]}")
            ],
        }

    tool_context = run_step_tools("plan_transport", state)
    try:
        content = await invoke_step_llm(
            "plan_transport",
            state,
            instruction=build_step_instruction(
                "plan_transport", state, _TRANSPORT_INSTRUCTION
            ),
            ctx=ctx,
        )
        grounding_errors = validate_transport_reply(content, tool_context or "")
        content = append_grounding_notice(content, grounding_errors)
    except Exception as exc:
        logger.exception("交通规划 LLM 调用失败")
        content = (
            f"暂时无法连接规划服务（{exc}）。"
            "请直接选择交通方式并在下一轮传入 selected_transport："
            "flight（航班）、train（高铁）、driving（自驾）。"
        )

    return {
        "current_step": "plan_transport",
        "messages": [AIMessage(content=content)],
    }
