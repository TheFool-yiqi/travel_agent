"""API v1 路由聚合（Handoffs：users / conversations / chat）。"""

from fastapi import APIRouter

from app.api.v1 import chat, itineraries, sessions, users
from app.api.v1.chat import router as chat_router
from app.api.v1.itineraries import router as itineraries_router
from app.api.v1.sessions import router as sessions_router
from app.api.v1.users import router as users_router
from app.ws.chat_stream import router as ws_chat_router

# Handoffs 模块别名：conversations → sessions
conversations = sessions

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(users.router)
api_v1_router.include_router(sessions.router, prefix="/sessions")
api_v1_router.include_router(conversations.router, prefix="/conversations")
api_v1_router.include_router(chat.router)
api_v1_router.include_router(itineraries.router)
api_v1_router.include_router(ws_chat_router)

__all__ = [
    "api_v1_router",
    "chat",
    "conversations",
    "itineraries",
    "sessions",
    "users",
    "chat_router",
    "itineraries_router",
    "sessions_router",
    "users_router",
    "ws_chat_router",
]
