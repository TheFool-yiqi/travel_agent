"""最终回复节点（对应 generate_order_tool）"""

import uuid

from langchain_core.messages import AIMessage

from app.graph.state import TravelState


def final_response(state: TravelState) -> dict:
    if state.get("order_id"):
        return {
            "current_step": "done",
            "messages": [AIMessage(content=f"订单已存在：{state['order_id']}")],
        }

    order_id = f"ORDER-{uuid.uuid4().hex[:8].upper()}"
    destination = state.get("selected_destination", "未知")
    budget_total = (state.get("budget") or {}).get("total", 0)

    return {
        "current_step": "done",
        "order_id": order_id,
        "messages": [
            AIMessage(
                content=(
                    f"订单生成成功！\n"
                    f"订单号：{order_id}\n"
                    f"目的地：{destination}\n"
                    f"预算：{budget_total:.2f} 元\n"
                    f"感谢使用 Travel Agent！"
                )
            )
        ],
    }
