"""行程审批节点（对话式确认，无 interrupt）"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from app.graph.routers.approval_router import (
    _last_user_text,
    user_wants_approval,
    user_wants_revision,
)
from app.graph.state import TravelState

_APPROVAL_PROMPT = (
    "行程与预算已生成，请查看右侧行程卡片。\n"
    "若满意请回复「确认」；如需调整请说明修改点或回复「修改行程」。"
)


async def approval_node(state: TravelState) -> dict:
    if not state.get("itinerary"):
        return {
            "current_step": "build_itinerary",
            "messages": [AIMessage(content="尚未生成行程，请先完成前面的规划步骤。")],
        }

    status = state.get("approval_status")
    if status == "approved":
        return {"current_step": "final_response"}

    user_text = _last_user_text(state)
    revision_note = user_text.strip()[:200] if user_text else ""
    revision_already_handled = bool(
        revision_note
        and state.get("consumed_revision_note") == revision_note
    )

    if user_text and user_wants_revision(user_text) and not revision_already_handled:
        return {
            "current_step": "revise_itinerary",
            "approval_status": "revising",
            "messages": [
                AIMessage(content="好的，将根据您的意见调整行程。")
            ],
        }

    if user_text and user_wants_approval(user_text):
        return {
            "current_step": "final_response",
            "approval_status": "approved",
            "consumed_revision_note": None,
            "messages": [
                AIMessage(content="已确认行程，正在生成订单…")
            ],
        }

    if status == "pending":
        return {
            "current_step": "approval_node",
            "approval_status": "pending",
            "messages": [
                AIMessage(
                    content=_APPROVAL_PROMPT
                    if revision_already_handled
                    else "仍在等待您的确认。回复「确认」通过，或说明需要修改的内容。"
                )
            ],
        }

    return {
        "current_step": "approval_node",
        "approval_status": "pending",
        "messages": [AIMessage(content=_APPROVAL_PROMPT)],
    }
