"""SSE / WebSocket 流式对话与消息持久化。"""



from __future__ import annotations



import asyncio
import contextlib
import json

import uuid

from collections.abc import AsyncIterator

from typing import Any



from langchain_core.messages import AIMessage, HumanMessage

from loguru import logger



from app.ai.llm import create_travel_planner

from app.db.models.message import Message

from app.db.models.travel_session import SESSION_STATUS_DELETED, TravelSession

from app.db.models.user import User

from app.db.repositories.message_repository import MessageRepository

from app.db.repositories.travel_session_repository import TravelSessionRepository

from app.db.session import get_session_factory

from app.graph.steps import PLANNING_STEPS, STEP_LABELS

from app.graph.greeting import build_greeting_reply, is_greeting_only_text
from app.graph.stream_callback import set_stream_token_handler
from app.services.conversation_bootstrap import has_assistant_messages

from app.services.itinerary_service import (
    approve_itinerary_with_order,
    upsert_itinerary_from_chat,
)



_GRAPH_NODE_NAMES = set(PLANNING_STEPS) | {"inject_user_memory", "revise_itinerary"}


def _assistant_text_from_node_output(output: Any) -> str | None:
    """从节点 output 中取最新一条 AIMessage（避免把历史助手消息拼接重复推送）。"""
    if not isinstance(output, dict):
        return None
    raw_messages = output.get("messages")
    if not raw_messages:
        return None
    for message in reversed(raw_messages):
        content: str | None = None
        if isinstance(message, AIMessage):
            raw = message.content
            content = raw if isinstance(raw, str) else str(raw) if raw is not None else None
        elif isinstance(message, dict):
            role = message.get("role") or message.get("type")
            if role in ("assistant", "ai"):
                raw = message.get("content")
                content = raw if isinstance(raw, str) else str(raw) if raw is not None else None
        if content and content.strip():
            return content.strip()
    return None


def _next_unique_token(assistant_message: str, token: str) -> str | None:
    """过滤已出现过的整段重复 token（尤其寒暄 prefetch + fallback）。"""
    if not token:
        return None
    if assistant_message.endswith(token):
        return None
    stripped = token.strip()
    if stripped and stripped in assistant_message:
        return None
    return token


def _drain_stream_tokens(queue: asyncio.Queue[str]) -> list[str]:
    tokens: list[str] = []
    while True:
        try:
            tokens.append(queue.get_nowait())
        except asyncio.QueueEmpty:
            break
    return tokens


async def _iter_graph_events_and_tokens(
    graph_events: AsyncIterator[dict[str, Any]],
    token_queue: asyncio.Queue[str],
) -> AsyncIterator[tuple[str, Any]]:
    """Multiplex LangGraph events with invoke_step_llm tokens during node execution."""
    graph_iter = graph_events.__aiter__()
    graph_task: asyncio.Task[Any] | None = None
    token_task: asyncio.Task[str] | None = None

    while True:
        if graph_task is None:
            graph_task = asyncio.create_task(graph_iter.__anext__())
        if token_task is None:
            token_task = asyncio.create_task(token_queue.get())

        done, _ = await asyncio.wait(
            {graph_task, token_task},
            return_when=asyncio.FIRST_COMPLETED,
        )

        if token_task in done:
            token = token_task.result()
            token_task = None
            yield ("token", token)

        if graph_task in done:
            try:
                event = graph_task.result()
            except StopAsyncIteration:
                graph_task = None
                break
            graph_task = None
            yield ("event", event)

    if token_task is not None:
        token_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await token_task

    for token in _drain_stream_tokens(token_queue):
        yield ("token", token)


def _should_emit_node_reply(
    *,
    node_streamed_tokens: bool,
    reply_text: str | None,
    assistant_message: str = "",
) -> bool:
    """Emit AIMessage fallback when the node did not stream tokens via invoke_step_llm."""
    if not reply_text or node_streamed_tokens:
        return False
    stripped = reply_text.strip()
    if not stripped:
        return False
    if stripped in assistant_message:
        return False
    return True


def _is_graph_node_chain_event(node_name: str) -> bool:
    """Only top-level graph nodes should drive step UI and reply fallback."""
    return node_name in _GRAPH_NODE_NAMES





def sse(data: dict[str, Any]) -> str:

    """SSE 标准 data 帧。"""

    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"





async def save_message(

    conversation_id: uuid.UUID,

    role: str,

    content: str,

    *,

    extra_info: dict[str, Any] | None = None,

) -> Message:

    """在独立会话中保存消息并提交。"""

    factory = get_session_factory()

    async with factory() as session:

        try:

            message = await MessageRepository(session).create(

                conversation_id=conversation_id,

                role=role,

                content=content,

                extra_info=extra_info,

            )

            await session.commit()

            return message

        except Exception:

            await session.rollback()

            raise





async def _load_travel_session(

    conversation_id: uuid.UUID,

    user_id: uuid.UUID,

) -> TravelSession | None:

    factory = get_session_factory()

    async with factory() as session:

        return await TravelSessionRepository(session).get_for_user(

            conversation_id, user_id

        )





async def _persist_itinerary_if_present(

    conversation_id: uuid.UUID,

    user: User,

    message_extra: dict[str, Any] | None,

) -> None:

    if not message_extra or "itinerary" not in message_extra:

        return

    days = message_extra.get("itinerary")

    if not isinstance(days, list):

        return

    budget = message_extra.get("budget")

    if budget is not None and not isinstance(budget, dict):

        budget = None

    summary = message_extra.get("summary")

    if summary is not None and not isinstance(summary, str):

        summary = None

    await upsert_itinerary_from_chat(

        conversation_id,

        user.id,

        days=days,

        budget=budget,

        summary=summary,

    )





async def _persist_order_if_present(

    conversation_id: uuid.UUID,

    user: User,

    message_extra: dict[str, Any] | None,

) -> None:

    if not message_extra:

        return

    order_id = message_extra.get("order_id")

    if not isinstance(order_id, str) or not order_id.strip():

        return

    await approve_itinerary_with_order(

        conversation_id,

        user.id,

        order_id=order_id.strip(),

    )





async def iter_chat_events(

    conversation_id: uuid.UUID,

    user_message: str,

    user: User,

) -> AsyncIterator[dict[str, Any]]:

    """LangGraph 规划流事件（dict，供 SSE / WebSocket 共用）。"""

    assistant_message = ""

    message_extra: dict[str, Any] | None = None



    travel_session = await _load_travel_session(conversation_id, user.id)

    if travel_session is None or travel_session.status == SESSION_STATUS_DELETED:

        yield {"type": "error", "message": "会话不存在"}

        return



    thread_id = travel_session.thread_id or str(travel_session.id)



    try:

        had_assistant_before = await has_assistant_messages(conversation_id)

        _, graph = await asyncio.gather(
            save_message(conversation_id, "user", user_message),
            create_travel_planner(),
        )

        greeting_prefetched = (
            is_greeting_only_text(user_message) and not had_assistant_before
        )
        if greeting_prefetched:
            yield {
                "type": "step",
                "step": "collect_requirements",
                "label": STEP_LABELS.get("collect_requirements", "collect_requirements"),
            }
            greeting = build_greeting_reply()
            yield {"type": "token", "content": greeting}
            assistant_message = greeting
            greeting_content_emitted = True
        else:
            greeting_content_emitted = False

        input_data = {

            "messages": [HumanMessage(content=user_message)],

            "user_id": str(user.id),

            "session_id": str(conversation_id),

        }

        config = {"configurable": {"thread_id": thread_id}}

        token_queue: asyncio.Queue[str] = asyncio.Queue()

        async def _enqueue_token(token: str) -> None:
            await token_queue.put(token)

        set_stream_token_handler(_enqueue_token)

        node_streamed_tokens = False

        try:

            graph_events = graph.astream_events(
                input_data,
                config=config,
                version="v2",
            )

            async for kind, payload in _iter_graph_events_and_tokens(
                graph_events,
                token_queue,
            ):
                if kind == "token":
                    token = _next_unique_token(assistant_message, payload)
                    if token is None:
                        continue
                    node_streamed_tokens = True
                    assistant_message += token
                    yield {"type": "token", "content": token}
                    continue

                event = payload
                event_kind = event.get("event")

                if event_kind == "on_tool_start":
                    yield {
                        "type": "tool_call",
                        "tool": event.get("name", ""),
                    }

                elif event_kind == "on_chain_start":
                    node_name = event.get("name", "")
                    if node_name in _GRAPH_NODE_NAMES:
                        node_streamed_tokens = greeting_prefetched and node_name == "collect_requirements"
                        if node_name == "inject_user_memory":
                            pass
                        elif greeting_prefetched and node_name == "collect_requirements":
                            pass
                        else:
                            yield {
                                "type": "step",
                                "step": node_name,
                                "label": STEP_LABELS.get(node_name, node_name),
                            }

                elif event_kind == "on_chain_end":
                    node_name = event.get("name", "")
                    if not _is_graph_node_chain_event(node_name):
                        continue
                    if greeting_content_emitted and node_name == "collect_requirements":
                        continue

                    output = event.get("data", {}).get("output")

                    if node_name == "collect_requirements" and isinstance(output, dict):
                        trace = output.get("semantic_trace")
                        if trace:
                            message_extra = dict(message_extra or {})
                            message_extra["semantic"] = trace

                    if node_name in PLANNING_STEPS and isinstance(output, dict):
                        itinerary = output.get("itinerary")
                        budget = output.get("budget")

                        if itinerary:
                            message_extra = dict(message_extra or {})
                            message_extra["itinerary"] = itinerary
                            message_extra["budget"] = budget
                            report = output.get("report")
                            if isinstance(report, str):
                                message_extra["summary"] = report
                            yield {
                                "type": "itinerary",
                                "itinerary": itinerary,
                                "budget": budget,
                            }

                        if (
                            node_name == "approval_node"
                            and output.get("approval_status") == "pending"
                        ):
                            yield {
                                "type": "approval_required",
                                "message": "请确认行程或提出修改意见",
                            }

                    if node_name == "final_response" and isinstance(output, dict):
                        order_id = output.get("order_id")
                        if isinstance(order_id, str) and order_id.strip():
                            message_extra = dict(message_extra or {})
                            message_extra["order_id"] = order_id.strip()
                            yield {
                                "type": "order",
                                "order_id": order_id.strip(),
                            }

                    reply_text = _assistant_text_from_node_output(output)
                    if _should_emit_node_reply(
                        node_streamed_tokens=node_streamed_tokens,
                        reply_text=reply_text,
                        assistant_message=assistant_message,
                    ):
                        token = _next_unique_token(
                            assistant_message,
                            f"\n\n{reply_text}" if assistant_message.strip() else reply_text,
                        )
                        if token is not None:
                            assistant_message += token
                            yield {"type": "token", "content": token}

                    node_streamed_tokens = False

        finally:

            set_stream_token_handler(None)



        if assistant_message.strip():

            await save_message(

                conversation_id,

                "assistant",

                assistant_message,

                extra_info=message_extra,

            )

            await _persist_itinerary_if_present(

                conversation_id,

                user,

                message_extra,

            )

            await _persist_order_if_present(

                conversation_id,

                user,

                message_extra,

            )



        yield {"type": "done"}



    except Exception as exc:

        logger.exception("流式对话错误 conversation_id={}", conversation_id)

        yield {"type": "error", "message": str(exc)}





async def generate_sse_stream(

    conversation_id: uuid.UUID,

    user_message: str,

    user: User,

) -> AsyncIterator[str]:

    """LangGraph 规划流 + SSE 事件。"""

    async for event in iter_chat_events(conversation_id, user_message, user):

        yield sse(event)

