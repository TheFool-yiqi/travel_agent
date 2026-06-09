"""EvidenceCard runtime schemas for PlanningRuntime retrieval."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

EvidenceCardStatus = Literal["temporary", "pending_review", "approved", "rejected"]
OnlineEvidenceCardStatus = Literal["approved"]
SuggestedAction = Literal["mark_assumptions_and_continue"]


class EvidenceCard(BaseModel):
    """Online retrieval result; V1 Runtime only consumes approved cards."""

    id: str
    claim: str
    evidence_type: str
    city: str | None = None
    entities: list[str] = Field(default_factory=list)
    applies_to: list[str] = Field(default_factory=list)
    time_hint: str | None = None
    intensity: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: OnlineEvidenceCardStatus = "approved"
    embedding_text: str
    source_document_id: str | None = None
    source_chunk_id: str | None = None

    @field_validator("status", mode="before")
    @classmethod
    def _require_approved_status(cls, value: Any) -> Any:
        if value != "approved":
            raise ValueError("Online EvidenceCard retrieval only accepts approved status")
        return value

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> EvidenceCard:
        return cls.model_validate(data)


class StoredEvidenceCard(BaseModel):
    """Repository/storage view; may include non-approved cards before filtering."""

    id: str
    claim: str
    evidence_type: str
    city: str | None = None
    entities: list[str] = Field(default_factory=list)
    applies_to: list[str] = Field(default_factory=list)
    time_hint: str | None = None
    intensity: str | None = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    status: EvidenceCardStatus = "pending_review"
    embedding_text: str
    source_document_id: str | None = None
    source_chunk_id: str | None = None

    def to_online_card(self) -> EvidenceCard:
        if self.status != "approved":
            raise ValueError(f"EvidenceCard {self.id} is not approved")
        return EvidenceCard(
            id=self.id,
            claim=self.claim,
            evidence_type=self.evidence_type,
            city=self.city,
            entities=list(self.entities),
            applies_to=list(self.applies_to),
            time_hint=self.time_hint,
            intensity=self.intensity,
            confidence=self.confidence,
            status="approved",
            embedding_text=self.embedding_text,
            source_document_id=self.source_document_id,
            source_chunk_id=self.source_chunk_id,
        )


class RetrievalTrace(BaseModel):
    vector_ranked_ids: list[str] = Field(default_factory=list)
    bm25_ranked_ids: list[str] = Field(default_factory=list)
    fused_ids: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> RetrievalTrace:
        return cls.model_validate(data)


class EvidenceContext(BaseModel):
    cards: list[EvidenceCard] = Field(default_factory=list)
    card_ids: list[str] = Field(default_factory=list)
    query_summary: dict[str, Any] = Field(default_factory=dict)
    retrieval_trace: RetrievalTrace = Field(default_factory=RetrievalTrace)

    def to_runtime_dict(self) -> dict[str, Any]:
        payload = self.model_dump(mode="json")
        return payload

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> EvidenceContext:
        trace = data.get("retrieval_trace")
        if isinstance(trace, dict):
            data = {**data, "retrieval_trace": RetrievalTrace.from_runtime_dict(trace)}
        return cls.model_validate(data)


class SufficiencyResult(BaseModel):
    is_sufficient: bool
    score: float = Field(ge=0.0, le=1.0)
    missing_tags: list[str] = Field(default_factory=list)
    missing_evidence_types: list[str] = Field(default_factory=list)
    suggested_action: SuggestedAction = "mark_assumptions_and_continue"

    @field_validator("suggested_action", mode="before")
    @classmethod
    def _require_v1_suggested_action(cls, value: Any) -> Any:
        if value != "mark_assumptions_and_continue":
            raise ValueError("V1 SufficiencyResult only supports mark_assumptions_and_continue")
        return value

    def to_runtime_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")

    @classmethod
    def from_runtime_dict(cls, data: dict[str, Any]) -> SufficiencyResult:
        return cls.model_validate(data)
