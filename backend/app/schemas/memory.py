"""长期记忆数据模型（用户画像 + 出行历史）"""

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class UserProfile(BaseModel):
    """用户画像：稳定偏好与个人信息"""

    travel_styles: list[str] = Field(
        default_factory=list,
        description="旅行风格，如：休闲度假、文化探索、户外冒险、美食之旅",
    )
    dietary_restrictions: list[str] = Field(
        default_factory=list,
        description="饮食禁忌，如：素食、清真、海鲜过敏",
    )
    food_preferences: list[str] = Field(
        default_factory=list,
        description="饮食偏好，如：辣、清淡、当地特色",
    )
    updated_at: Optional[str] = Field(default=None, description="最后更新时间")


class TravelRecord(BaseModel):
    """单次已完成旅行"""

    destination: str = Field(..., description="目的地")
    start_date: str = Field(..., description="开始日期 YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期 YYYY-MM-DD")
    visited_attractions: list[str] = Field(
        default_factory=list,
        description="本次游玩景点",
    )


class AccommodationPreference(BaseModel):
    """住宿偏好"""

    preferred_types: list[str] = Field(
        default_factory=list,
        description="偏好类型，如：星级酒店、经济酒店、特色民宿",
    )
    avg_budget_per_night: Optional[float] = Field(
        default=None,
        description="平均每晚预算（元）",
    )


class TravelHistory(BaseModel):
    """出行历史：已完成行程与住宿偏好"""

    completed_trips: list[TravelRecord] = Field(
        default_factory=list,
        description="已完成旅行记录",
    )
    visited_attractions: list[str] = Field(
        default_factory=list,
        description="去过的景点汇总，用于避免重复推荐",
    )
    accommodation_preference: AccommodationPreference = Field(
        default_factory=AccommodationPreference,
        description="住宿偏好",
    )
    updated_at: Optional[str] = Field(default=None, description="最后更新时间")


class UserMemory(BaseModel):
    """用户完整长期记忆"""

    user_id: str = Field(..., description="用户唯一标识")
    profile: UserProfile = Field(default_factory=UserProfile)
    history: TravelHistory = Field(default_factory=TravelHistory)

    def to_prompt_context(self) -> str:
        """格式化为可注入 Agent / Graph 的文本上下文"""
        lines = [f"用户 ID: {self.user_id}"]

        if self.profile.travel_styles:
            lines.append(f"旅行风格: {', '.join(self.profile.travel_styles)}")
        if self.profile.dietary_restrictions:
            lines.append(f"饮食禁忌: {', '.join(self.profile.dietary_restrictions)}")
        if self.profile.food_preferences:
            lines.append(f"饮食偏好: {', '.join(self.profile.food_preferences)}")
        if self.history.visited_attractions:
            lines.append(
                f"已去过景点: {', '.join(self.history.visited_attractions)}"
            )

        pref = self.history.accommodation_preference
        if pref.preferred_types:
            lines.append(f"住宿偏好: {', '.join(pref.preferred_types)}")
        if pref.avg_budget_per_night is not None:
            lines.append(f"平均每晚住宿预算: {pref.avg_budget_per_night} 元")

        return "\n".join(lines)


def empty_user_memory(user_id: str) -> UserMemory:
    """创建空的用户长期记忆"""
    return UserMemory(user_id=user_id)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
