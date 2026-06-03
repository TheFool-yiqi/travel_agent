"""Pydantic 请求/响应与领域模型"""

from app.schemas.memory import (
    AccommodationPreference,
    TravelHistory,
    TravelRecord,
    UserMemory,
    UserProfile,
)
from app.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationUpdate,
    TravelSessionResponse,
)
from app.schemas.message import MessageCreate, MessageResponse
from app.schemas.travel import BudgetBreakdown, UserRequirement
from app.schemas.user import TokenResponse, UserLogin, UserRegister, UserResponse

__all__ = [
    "AccommodationPreference",
    "BudgetBreakdown",
    "ConversationCreate",
    "ConversationResponse",
    "ConversationUpdate",
    "MessageCreate",
    "MessageResponse",
    "TokenResponse",
    "TravelHistory",
    "TravelSessionResponse",
    "TravelRecord",
    "UserLogin",
    "UserMemory",
    "UserProfile",
    "UserRegister",
    "UserRequirement",
    "UserResponse",
]
