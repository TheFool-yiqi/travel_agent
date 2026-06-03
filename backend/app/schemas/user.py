"""用户 API 请求/响应模型。"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegister(BaseModel):
    """用户注册"""

    username: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    """用户登录（用户名 + 密码）"""

    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1)


class UserResponse(BaseModel):
    """用户信息响应（不含 password_hash）"""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    preferences: dict[str, Any] | None = None
    display_name: str | None = None
    is_active: bool = True
    created_at: datetime


class TokenResponse(BaseModel):
    """登录成功：JWT + 用户信息"""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse
