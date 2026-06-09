"""step_context 窗口化与 memory_context 注入测试。"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.graph.nodes.inject_memory import inject_user_memory
from app.graph.step_context import DIALOGUE_WINDOW_SIZE, build_step_messages


@pytest.mark.asyncio
async def test_inject_user_memory_does_not_append_system_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "app.graph.nodes.inject_memory.format_user_memory_for_prompt",
        AsyncMock(return_value="偏好：文化游"),
    )
    state = {
        "user_id": str(uuid.uuid4()),
        "messages": [HumanMessage(content="我想去成都")],
    }

    first = await inject_user_memory(state)
    second = await inject_user_memory({**state, **first})

    assert "messages" not in first
    assert "messages" not in second
    assert first["memory_context"] == "偏好：文化游"
    assert second["memory_context"] == "偏好：文化游"


def test_build_step_messages_includes_memory_context_once() -> None:
    messages = [
        HumanMessage(content="你好"),
        AIMessage(content="你好，请问目的地？"),
    ]
    state = {
        "messages": messages,
        "memory_context": "偏好：亲子游",
    }

    built = build_step_messages("步骤 system", state)

    system_prompts = [m for m in built if isinstance(m, SystemMessage)]
    assert len(system_prompts) == 2
    assert system_prompts[0].content == "步骤 system"
    assert system_prompts[1].content == "偏好：亲子游"
    assert built[-1].content == "你好，请问目的地？"


def test_build_step_messages_windows_dialogue() -> None:
    dialogue = [HumanMessage(content=f"msg-{index}") for index in range(DIALOGUE_WINDOW_SIZE + 5)]
    state = {"messages": dialogue, "memory_context": "mem"}

    built = build_step_messages("sys", state)
    human_messages = [m for m in built if isinstance(m, HumanMessage)]

    assert len(human_messages) == DIALOGUE_WINDOW_SIZE
    assert human_messages[0].content == "msg-5"
    assert human_messages[-1].content == f"msg-{DIALOGUE_WINDOW_SIZE + 4}"
