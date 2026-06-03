"""用户管理 API（/api/v1/users）。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.models.user import User
from app.db.repositories.user_repository import UserRepository
from app.db.session import get_db
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/users", tags=["用户管理"])


def _token_response(user: User) -> TokenResponse:
    access_token = create_access_token(
        {"sub": str(user.id), "username": user.username},
    )
    return TokenResponse(
        access_token=access_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """用户注册"""
    repo = UserRepository(db)

    if await repo.get_by_username(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在",
        )

    if await repo.get_by_email(str(user_data.email)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册",
        )

    user = await repo.create(
        username=user_data.username,
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
        preferences={},
    )
    return _token_response(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """用户登录"""
    user = await UserRepository(db).get_by_username(credentials.username)

    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已停用",
        )

    return _token_response(user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: User = Depends(get_current_user),
) -> UserResponse:
    """获取当前用户信息"""
    return UserResponse.model_validate(user)
