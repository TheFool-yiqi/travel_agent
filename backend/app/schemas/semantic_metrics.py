"""语义理解质量指标 API 响应。"""

from pydantic import BaseModel, Field


class SemanticMetricsResponse(BaseModel):
    turns: int = 0
    slot_filled_turns: int = 0
    first_hit_turns: int = 0
    clarification_turns: int = 0
    clarification_resolved_turns: int = 0
    user_correction_turns: int = 0
    first_hit_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    clarification_rate: float = Field(default=0.0, ge=0.0, le=1.0)
    planning_reached: bool = False
