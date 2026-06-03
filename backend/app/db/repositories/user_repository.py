"""User persistence."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(User).where(User.email == email)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        stmt = select(User).where(User.username == username)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        username: str,
        email: str,
        password_hash: str,
        preferences: dict | None = None,
        display_name: str | None = None,
        is_active: bool = True,
    ) -> User:
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            preferences=preferences or {},
            display_name=display_name,
            is_active=is_active,
        )
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update_preferences(self, user_id: uuid.UUID, preferences: dict) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        user.preferences = {**(user.preferences or {}), **preferences}
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def list_active(self, *, limit: int = 100, offset: int = 0) -> list[User]:
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
