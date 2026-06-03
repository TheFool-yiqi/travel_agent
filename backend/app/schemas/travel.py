"""旅行规划领域模型（与 TravelState 字段对齐）"""

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

TravelStyle = Literal["relaxation", "culture", "adventure", "food"]
BudgetLevel = Literal["economy", "comfort", "luxury"]
TransportType = Literal["flight", "train", "driving"]
AccommodationType = Literal["star_hotel", "economy_hotel", "hostel", "youth_hostel"]
FoodType = Literal["specialty", "chain", "local"]

VALID_TRANSPORT = {"flight", "train", "driving"}
VALID_ACCOMMODATION = {"star_hotel", "economy_hotel", "hostel", "youth_hostel"}
VALID_FOOD = {"specialty", "chain", "local"}
VALID_ACTIVITY = {"culture", "nature", "food_tour", "shopping", "family_fun"}
ActivityType = Literal["culture", "nature", "food_tour", "shopping", "family_fun"]


class UserRequirement(BaseModel):
    """用户旅行需求"""

    departure_city: str
    destination: Optional[str] = None
    departure_date: str = Field(description="YYYY-MM-DD")
    travel_days: int = Field(ge=1)
    adult_count: int = Field(default=1, ge=1)
    children_count: int = Field(default=0, ge=0)
    budget_min: float = Field(ge=0)
    budget_max: float = Field(ge=0)
    budget_level: BudgetLevel = "comfort"
    travel_styles: list[str] = Field(default_factory=list)
    special_needs: Optional[str] = None

    @field_validator("departure_date")
    @classmethod
    def validate_date(cls, value: str) -> str:
        from datetime import datetime

        datetime.strptime(value, "%Y-%m-%d")
        return value


class BudgetBreakdown(BaseModel):
    """预算明细"""

    transport: float = 0
    accommodation: float = 0
    food: float = 0
    attractions: float = 0
    misc: float = 0
    total: float = 0


def infer_budget_level(budget_min: float, budget_max: float) -> BudgetLevel:
    avg = (budget_min + budget_max) / 2
    if avg < 3000:
        return "economy"
    if avg < 8000:
        return "comfort"
    return "luxury"


class RequirementExtraction(BaseModel):
    """从对话中提取的旅行需求字段（LLM structured output）。"""

    departure_city: Optional[str] = None
    departure_date: Optional[str] = None
    travel_days: Optional[int] = Field(default=None, ge=1)
    adult_count: Optional[int] = Field(default=None, ge=1)
    children_count: Optional[int] = Field(default=None, ge=0)
    budget_min: Optional[float] = Field(default=None, ge=0)
    budget_max: Optional[float] = Field(default=None, ge=0)
    destination: Optional[str] = None
    travel_styles: list[str] = Field(default_factory=list)
    special_needs: Optional[str] = None
    user_confirmed: bool = False

    @field_validator("travel_styles", mode="before")
    @classmethod
    def _coerce_travel_styles(cls, value: list[str] | None) -> list[str]:
        return value or []

    @field_validator("special_needs", mode="before")
    @classmethod
    def _coerce_special_needs(cls, value: str | list | None) -> str | None:
        if value is None:
            return None
        if isinstance(value, list):
            parts = [str(item).strip() for item in value if str(item).strip()]
            return "；".join(parts) if parts else None
        text = str(value).strip()
        return text or None


class DayPlan(BaseModel):
    """单日行程安排。"""

    day_number: int = Field(ge=1)
    theme: str = ""
    morning: str
    afternoon: str
    evening: str
    meals: list[str] = Field(default_factory=list)
    accommodation: str = ""
    plan_b: Optional[str] = None


class ItineraryBuildResult(BaseModel):
    """行程与预算结构化输出。"""

    summary: str
    days: list[DayPlan]
    budget: BudgetBreakdown


class PlanningSelectionExtraction(BaseModel):
    """从对话中提取分步选择（目的地 / 交通 / 食宿偏好）。"""

    selected_destination: Optional[str] = None
    selected_transport: Optional[TransportType] = None
    selected_accommodation_types: list[AccommodationType] = Field(default_factory=list)
    selected_food_types: list[FoodType] = Field(default_factory=list)
    selected_activity_types: list[ActivityType] = Field(default_factory=list)

    @field_validator(
        "selected_accommodation_types",
        "selected_food_types",
        "selected_activity_types",
        mode="before",
    )
    @classmethod
    def _coerce_list_fields(cls, value: list[str] | None) -> list[str]:
        return value or []

    @field_validator("selected_transport", mode="before")
    @classmethod
    def _coerce_selected_transport(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text not in VALID_TRANSPORT:
            return None
        return text
