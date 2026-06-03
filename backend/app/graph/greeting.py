"""纯寒暄检测与即时回复（跳过 LLM，降低首条消息延迟）"""

from __future__ import annotations

import re

from langchain_core.messages import BaseMessage, HumanMessage

_GREETING_ONLY = re.compile(
    r"^(你好|您好|hi|hello|hey|在吗|nihao|哈喽)[!.?？！\s]*$",
    re.IGNORECASE,
)


def build_greeting_reply() -> str:
    """即时问候：只引导第一项（目的地），不混问时间/出发地。"""
    return (
        "嗨！我是你的旅行顾问。"
        "先聊聊你想去哪里玩吧？（例如：成都、杭州、三亚）"
    )


# 兼容旧引用；动态内容请用 build_greeting_reply()
GREETING_REPLY = build_greeting_reply()


def is_greeting_only_text(text: str) -> bool:
    return bool(_GREETING_ONLY.match(text.strip()))


def is_greeting_only_messages(messages: list[BaseMessage]) -> bool:
    for message in reversed(messages):
        if isinstance(message, HumanMessage):
            content = message.content if isinstance(message.content, str) else str(message.content)
            return is_greeting_only_text(content)
    return False
