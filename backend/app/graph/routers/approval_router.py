"""审批与修订路由"""

import re

from langgraph.graph import END

from app.graph.state import TravelState

APPROVE_KEYWORDS = (
    "确认",
    "同意",
    "可以",
    "没问题",
    "好的",
    "ok",
    "approve",
    "通过",
)

REVISE_KEYWORDS = (
    "修改",
    "改一下",
    "调整",
    "重新",
    "不满意",
    "换",
    "revise",
    "change",
    "改行程",
)


def _last_user_text(state: TravelState) -> str:
    from langchain_core.messages import HumanMessage

    messages = state.get("messages") or []
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content
            if isinstance(content, str):
                return content.strip()
            return str(content).strip()
    return ""


def user_wants_approval(text: str) -> bool:
    lower = text.lower()
    return any(keyword in text or keyword in lower for keyword in APPROVE_KEYWORDS)


def user_wants_revision(text: str) -> bool:
    lower = text.lower()
    if any(keyword in text or keyword in lower for keyword in REVISE_KEYWORDS):
        return True
    return bool(re.search(r"改[\u4e00-\u9fff]{1,8}", text))


def route_after_itinerary(state: TravelState) -> str:
    """行程生成后进入审批，或等待补全信息。"""
    if state.get("itinerary") and state.get("current_step") == "approval_node":
        return "approval_node"
    return END


def route_after_approval(state: TravelState) -> str:
    step = state.get("current_step")
    if step == "final_response":
        return "final_response"
    if step == "revise_itinerary":
        return "revise_itinerary"
    return END
