"""行程修订节点（轻量：清空审批并回到行程生成）"""

from __future__ import annotations

from langchain_core.messages import AIMessage

from app.graph.routers.approval_router import _last_user_text
from app.graph.state import TravelState


async def revise_itinerary(state: TravelState) -> dict:
    user_text = _last_user_text(state) or "用户希望调整行程"
    note = user_text[:200]

    return {
        "current_step": "build_itinerary",
        "approval_status": None,
        "itinerary": [],
        "budget": {},
        "report": f"修订说明：{note}",
        "consumed_revision_note": note,
        "messages": [
            AIMessage(
                content=f"收到修改意见：「{note}」。正在重新生成行程与预算…"
            )
        ],
    }
