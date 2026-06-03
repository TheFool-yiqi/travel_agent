"""WebSocket 流式对话（与 SSE 共享 iter_chat_events）。"""

from __future__ import annotations

import asyncio
import json
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_session_factory
from app.security.jwt import decode_access_token
from app.services.chat_stream import iter_chat_events

router = APIRouter(prefix="/chat", tags=["对话"])


async def _user_from_token(token: str, db: AsyncSession) -> User | None:
    payload = decode_access_token(token)
    if payload is None:
        return None
    sub = payload.get("sub")
    if sub is None:
        return None
    try:
        user_id = uuid.UUID(str(sub))
    except (ValueError, TypeError):
        return None
    user = await UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        return None
    return user


async def authenticate_websocket(websocket: WebSocket) -> User | None:
    """Query ?token= 或首帧 {"type":"auth","token":"..."}。"""
    query_token = websocket.query_params.get("token")
    factory = get_session_factory()

    if query_token:
        async with factory() as db:
            user = await _user_from_token(query_token, db)
        if user is None:
            await websocket.close(code=4401, reason="令牌无效或已过期")
            return None
        await websocket.accept()
        return user

    await websocket.accept()
    try:
        first = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
    except (TimeoutError, WebSocketDisconnect, json.JSONDecodeError, ValueError):
        await websocket.close(code=4401, reason="认证超时或格式错误")
        return None

    if first.get("type") != "auth" or not first.get("token"):
        await websocket.close(code=4401, reason="需要认证帧")
        return None

    async with factory() as db:
        user = await _user_from_token(str(first["token"]), db)
    if user is None:
        await websocket.close(code=4401, reason="令牌无效或已过期")
        return None
    return user


def _parse_conversation_id(conversation_id: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(conversation_id)
    except ValueError:
        return None


@router.websocket("/ws/{conversation_id}")
async def websocket_chat(websocket: WebSocket, conversation_id: str) -> None:
    """WebSocket 流式对话（JSON 帧，事件格式同 SSE data）。"""
    user = await authenticate_websocket(websocket)
    if user is None:
        return

    cid = _parse_conversation_id(conversation_id)
    if cid is None:
        await websocket.send_json({"type": "error", "message": "无效的会话 ID"})
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    try:
        while True:
            payload = await websocket.receive_json()
            msg_type = payload.get("type")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if msg_type != "message":
                await websocket.send_json({
                    "type": "error",
                    "message": "未知消息类型，请发送 type=message",
                })
                continue

            content = str(payload.get("content", "")).strip()
            if not content:
                await websocket.send_json({"type": "error", "message": "消息内容不能为空"})
                continue

            async for event in iter_chat_events(cid, content, user):
                await websocket.send_json(event)
                if event.get("type") in {"done", "error"}:
                    break

    except WebSocketDisconnect:
        logger.debug("WebSocket 断开 conversation_id={}", conversation_id)
    except Exception as exc:
        logger.exception("WebSocket 流式对话错误 conversation_id={}", conversation_id)
        try:
            await websocket.send_json({"type": "error", "message": str(exc)})
        except Exception:
            pass
