"""PlanningRuntime-backed chat streaming for SSE / WebSocket."""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import AsyncIterator
from typing import Any

from loguru import logger

from app.db.models.travel_session import SESSION_STATUS_DELETED
from app.db.models.user import User
from app.db.repositories.travel_session_repository import TravelSessionRepository
from app.db.session import get_session_factory
from app.runtime.planning_runtime import PlanningRuntime
from app.runtime.session_state import (
    RUNTIME_STATE_KEY,
    append_assistant_public_message,
    load_runtime_state_from_session,
    prepare_runtime_turn,
    runtime_state_to_session_payload,
)
from app.runtime.stages.base import build_production_stage_handlers
from app.runtime.state import RuntimeState
from app.services.chat_stream import (
    _persist_itinerary_if_present,
    _persist_order_if_present,
    save_message,
)
from app.services.runtime_chat_stream import iter_frontend_transport_events


async def _load_travel_session(conversation_id: uuid.UUID, user_id: uuid.UUID):
    factory = get_session_factory()
    async with factory() as session:
        return await TravelSessionRepository(session).get_for_user(
            conversation_id,
            user_id,
        )


async def _persist_runtime_state_to_session(
    conversation_id: uuid.UUID,
    user_id: uuid.UUID,
    runtime_state: RuntimeState,
) -> None:
    factory = get_session_factory()
    async with factory() as session:
        repo = TravelSessionRepository(session)
        travel_session = await repo.get_for_user(conversation_id, user_id)
        if travel_session is None:
            return
        extra_info = dict(travel_session.extra_info or {})
        extra_info[RUNTIME_STATE_KEY] = runtime_state_to_session_payload(runtime_state)
        await repo.update(travel_session, extra_info=extra_info)
        await session.commit()


def _merge_transport_extra(
    message_extra: dict[str, Any] | None,
    event: dict[str, Any],
) -> dict[str, Any] | None:
    event_type = event.get("type")
    if event_type == "itinerary":
        message_extra = dict(message_extra or {})
        message_extra["itinerary"] = event.get("itinerary")
        message_extra["budget"] = event.get("budget")
        draft = event.get("itinerary")
        if isinstance(draft, list) and draft:
            message_extra.setdefault("summary", "行程草案已生成")
        return message_extra
    if event_type == "order":
        order_id = event.get("order_id")
        if isinstance(order_id, str) and order_id.strip():
            message_extra = dict(message_extra or {})
            message_extra["order_id"] = order_id.strip()
        return message_extra
    return message_extra


async def iter_chat_events_runtime(
    conversation_id: uuid.UUID,
    user_message: str,
    user: User,
) -> AsyncIterator[dict[str, Any]]:
    """PlanningRuntime chat stream mapped to the existing frontend transport contract."""
    assistant_message = ""
    message_extra: dict[str, Any] | None = None

    travel_session = await _load_travel_session(conversation_id, user.id)
    if travel_session is None or travel_session.status == SESSION_STATUS_DELETED:
        yield {"type": "error", "message": "会话不存在"}
        return

    try:
        await save_message(conversation_id, "user", user_message)

        run_id = str(uuid.uuid4())
        runtime_state = load_runtime_state_from_session(
            travel_session.extra_info,
            run_id=run_id,
            conversation_id=str(conversation_id),
            user_id=str(user.id),
            input_message=user_message,
        )
        runtime_state = prepare_runtime_turn(
            runtime_state,
            input_message=user_message,
            user_message_record={"role": "user", "content": user_message},
        )

        runtime = PlanningRuntime(build_production_stage_handlers())
        token_queue: asyncio.Queue[str] = asyncio.Queue()
        saw_done = False

        async for event in iter_frontend_transport_events(runtime.run(runtime_state), token_queue):
            if event.get("type") == "done":
                saw_done = True
            if event.get("type") == "token":
                content = str(event.get("content") or "")
                if content:
                    assistant_message += content
            message_extra = _merge_transport_extra(message_extra, event)
            yield event

        final_state = runtime.last_state
        if final_state is not None:
            if assistant_message.strip():
                final_state = append_assistant_public_message(
                    final_state,
                    content=assistant_message,
                )
            await _persist_runtime_state_to_session(
                conversation_id,
                user.id,
                final_state,
            )

        if assistant_message.strip():
            await save_message(
                conversation_id,
                "assistant",
                assistant_message,
                extra_info=message_extra,
            )
            await _persist_itinerary_if_present(conversation_id, user, message_extra)
            await _persist_order_if_present(conversation_id, user, message_extra)

        if not saw_done:
            yield {"type": "done"}

    except Exception as exc:
        logger.exception("Runtime 流式对话错误 conversation_id={}", conversation_id)
        yield {"type": "error", "message": str(exc)}
