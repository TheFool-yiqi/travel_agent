"""LangGraph 全局状态定义"""

from typing import Annotated, Any, Optional

from langchain_core.messages import AnyMessage
from typing_extensions import TypedDict

from app.graph.reducers import add_messages
from app.graph.transport_state import (
    DrivingRoute,
    FlightOption,
    TrainOption,
    TransportState,
    TransportType,
)

__all__ = [
    "TravelState",
    "TransportType",
    "FlightOption",
    "TrainOption",
    "DrivingRoute",
]


class TravelState(TransportState, TypedDict, total=False):
    """
    旅行规划 Graph 状态

    节点通过 return dict 做 partial update，不要原地修改 state。
    """

    messages: Annotated[list[AnyMessage], add_messages]
    memory_context: Optional[str]
    current_step: str
    user_id: str
    session_id: str

    # 需求收集（collect_requirements）
    user_requirement: dict[str, Any]
    requirements_complete: bool
    departure_city: Optional[str]
    departure_date: Optional[str]
    travel_days: Optional[int]
    adult_count: Optional[int]
    children_count: Optional[int]
    party_confirmed: bool
    budget_min: Optional[float]
    budget_max: Optional[float]
    travel_styles: list[str]
    special_needs: Optional[str]

    user_confirmed: bool

    pending_clarification: Optional[dict[str, Any]]
    semantic_trace: Optional[dict[str, Any]]

    # 兼容简写字段
    destination: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]

    # 分步选择
    selected_destination: Optional[str]
    selected_transport: Optional[TransportType]
    selected_accommodation_types: list[str]
    selected_food_types: list[str]
    selected_activity_types: list[str]

    # 输出
    itinerary: list[dict[str, Any]]
    budget: dict[str, Any]
    order_id: Optional[str]
    report: Optional[str]

    approval_status: Optional[str]
    consumed_revision_note: Optional[str]
    error: Optional[str]
