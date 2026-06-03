"""流式对话 API（SSE）与历史消息。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.travel_session import SESSION_STATUS_DELETED
from app.db.models.user import User
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.travel_session_repository import TravelSessionRepository
from app.db.session import get_db
from app.schemas.conversation import ConversationResponse
from app.schemas.message import MessageCreate, MessageResponse
from app.services.chat_stream import generate_sse_stream

router = APIRouter(prefix="/chat", tags=["对话"])


def _parse_conversation_id(conversation_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(conversation_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话 ID",
        ) from exc


@router.post("/stream/{conversation_id}")
async def stream_chat(
    conversation_id: str,
    data: MessageCreate,
    user: User = Depends(get_current_user),
) -> StreamingResponse:
    """流式对话（SSE）。"""
    cid = _parse_conversation_id(conversation_id)
    return StreamingResponse(
        generate_sse_stream(cid, data.content, user),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """获取会话历史消息。"""
    cid = _parse_conversation_id(conversation_id)
    session_repo = TravelSessionRepository(db)
    travel_session = await session_repo.get_for_user(cid, user.id)

    if travel_session is None or travel_session.status == SESSION_STATUS_DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    messages = await MessageRepository(db).list_for_conversation(cid)
    return {
        "conversation": ConversationResponse.model_validate(travel_session).model_dump(),
        "messages": [
            MessageResponse.model_validate(m).model_dump() for m in messages
        ],
    }
