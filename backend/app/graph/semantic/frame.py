"""语义理解结构化输出模型。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ExtractionSource = Literal["rule", "fuzzy", "llm", "hybrid"]


class TextCorrection(BaseModel):
    original: str
    corrected: str
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)


class SemanticFrame(BaseModel):
    """单轮用户输入的语义解析结果。"""

    normalized_text: str = ""
    corrections: list[TextCorrection] = Field(default_factory=list)
    slot_updates: dict[str, Any] = Field(default_factory=dict)
    ambiguities: list[dict[str, Any]] = Field(default_factory=list)
    guidance_step: str = ""
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    extraction_source: ExtractionSource = "rule"
    reply_override: str | None = None
    pending_clarification: dict[str, Any] | None = None
    pending_clarification_cleared: bool = False

    def to_trace(self, *, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        """写入 message extra_info 的可序列化摘要。"""
        payload: dict[str, Any] = {
            "normalized_text": self.normalized_text,
            "corrections": [item.model_dump() for item in self.corrections],
            "slot_updates": self.slot_updates,
            "ambiguities": self.ambiguities,
            "guidance_step": self.guidance_step,
            "confidence": self.confidence,
            "extraction_source": self.extraction_source,
        }
        if metrics:
            payload["metrics"] = metrics
        return payload
