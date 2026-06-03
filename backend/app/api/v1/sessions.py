"""会话管理 API（ORM：TravelSession；Handoffs 路径 /conversations，文档路径 /sessions）。"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.travel_session import SESSION_STATUS_DELETED
from app.db.models.user import User
from app.db.repositories.message_repository import MessageRepository
from app.db.repositories.travel_session_repository import TravelSessionRepository
from app.db.session import get_db
from app.graph.semantic.semantic_metrics import (
    aggregate_session_metrics,
    extract_traces_from_messages,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
)
from app.schemas.semantic_metrics import SemanticMetricsResponse
from app.services.conversation_bootstrap import seed_initial_greeting

router = APIRouter(tags=["会话管理"])


def _parse_session_id(session_id: str) -> uuid.UUID:
    try:
        return uuid.UUID(session_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的会话 ID",
        ) from exc


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    data: ConversationCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """创建新会话"""
    repo = TravelSessionRepository(db)
    session = await repo.create(
        user_id=user.id,
        title=data.title or "新对话",
        extra_info=data.extra_info,
        thread_id=data.thread_id,
    )
    await seed_initial_greeting(db, session.id)
    return ConversationResponse.model_validate(session)


@router.get("", response_model=list[ConversationResponse])
async def list_conversations(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConversationResponse]:
    """获取当前用户的会话列表（不含已软删除）"""
    repo = TravelSessionRepository(db)
    sessions = await repo.list_for_user(user.id, exclude_deleted=True)
    return [ConversationResponse.model_validate(s) for s in sessions]


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """获取会话详情"""
    sid = _parse_session_id(conversation_id)
    session = await TravelSessionRepository(db).get_for_user(sid, user.id)
    if session is None or session.status == SESSION_STATUS_DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )
    return ConversationResponse.model_validate(session)


@router.get("/{conversation_id}/semantic-metrics", response_model=SemanticMetricsResponse)
async def get_semantic_metrics(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> SemanticMetricsResponse:
    """会话语义理解质量指标（槽位命中率、澄清轮次等）。"""
    sid = _parse_session_id(conversation_id)
    session = await TravelSessionRepository(db).get_for_user(sid, user.id)
    if session is None or session.status == SESSION_STATUS_DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    messages = await MessageRepository(db).list_for_conversation(sid)
    traces = extract_traces_from_messages(messages)
    return SemanticMetricsResponse.model_validate(aggregate_session_metrics(traces))


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    data: ConversationUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """更新会话"""
    sid = _parse_session_id(conversation_id)
    repo = TravelSessionRepository(db)
    session = await repo.get_for_user(sid, user.id)
    if session is None or session.status == SESSION_STATUS_DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    session = await repo.update(
        session,
        title=data.title,
        status=data.status,
        extra_info=data.extra_info,
    )
    return ConversationResponse.model_validate(session)


@router.delete("/{conversation_id}", status_code=status.HTTP_200_OK)
async def delete_conversation(
    conversation_id: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """删除会话（软删除）"""
    sid = _parse_session_id(conversation_id)
    repo = TravelSessionRepository(db)
    session = await repo.get_for_user(sid, user.id)
    if session is None or session.status == SESSION_STATUS_DELETED:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在",
        )

    await repo.update(session, status=SESSION_STATUS_DELETED)
    return {"message": "会话已删除"}
