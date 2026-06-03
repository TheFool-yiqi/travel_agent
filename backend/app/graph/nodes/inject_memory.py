"""调 LLM 前注入用户长期记忆（Middleware 等价节点）"""

from langchain_core.messages import SystemMessage

from app.dependencies import format_user_memory_for_prompt
from app.graph.greeting import is_greeting_only_messages
from app.graph.state import TravelState


async def inject_user_memory(state: TravelState) -> dict:
    """
    从 Store 读取长期记忆，注入 messages。

    等价于 @before_model middleware：每次进入 Graph 时刷新用户偏好上下文。
    """
    messages = state.get("messages") or []
    if is_greeting_only_messages(messages):
        return {}

    user_id = state.get("user_id")
    if not user_id:
        return {}

    memory_text = await format_user_memory_for_prompt(user_id)
    if not memory_text:
        return {}

    return {
        "messages": [SystemMessage(content=memory_text)],
    }
