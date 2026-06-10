"""Quality verification schemas."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

IssueSeverity = Literal["info", "warning", "blocking"]
SuggestedAction = Literal["continue", "surface_to_user", "request_revision"]


class QualityIssue(BaseModel):
    code: str
    message: str
    severity: IssueSeverity
    field: str | None = None

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> QualityIssue:
        return cls.model_validate(data)


class QualityReport(BaseModel):
    is_acceptable: bool
    has_blocking_issues: bool
    score: float = Field(ge=0.0, le=1.0)
    issues: list[QualityIssue] = Field(default_factory=list)
    unsupported_claims: list[str] = Field(default_factory=list)
    revision_applied: bool = False
    suggested_action: SuggestedAction = "continue"
    verified_at: str | None = None

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> QualityReport:
        issues = data.get("issues")
        if isinstance(issues, list):
            data = {
                **data,
                "issues": [
                    QualityIssue.from_runtime_dict(item)
                    if isinstance(item, dict)
                    else item
                    for item in issues
                ],
            }
        return cls.model_validate(data)
