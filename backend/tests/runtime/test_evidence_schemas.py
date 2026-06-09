"""Evidence schema contract tests."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.knowledge.evidence_schemas import (
    EvidenceCard,
    EvidenceContext,
    RetrievalTrace,
    StoredEvidenceCard,
    SufficiencyResult,
)


def _approved_card_dict() -> dict:
    return {
        "id": "card_1",
        "claim": "武侯祠和锦里适合组合为半日文化游",
        "evidence_type": "route_relation",
        "city": "成都",
        "entities": ["武侯祠", "锦里"],
        "applies_to": ["第一次到访", "低强度"],
        "time_hint": "半日",
        "intensity": "低",
        "confidence": 0.92,
        "status": "approved",
        "embedding_text": "城市：成都 武侯祠 锦里 半日 低强度",
        "source_document_id": "doc_1",
        "source_chunk_id": "chunk_1",
    }


def test_evidence_card_round_trip() -> None:
    card = EvidenceCard.from_runtime_dict(_approved_card_dict())
    restored = EvidenceCard.from_runtime_dict(card.to_runtime_dict())

    assert restored == card
    assert restored.status == "approved"


def test_evidence_card_rejects_non_approved_status() -> None:
    payload = _approved_card_dict()
    payload["status"] = "pending_review"

    with pytest.raises(ValidationError, match="approved"):
        EvidenceCard.from_runtime_dict(payload)


def test_stored_evidence_card_to_online_requires_approved() -> None:
    stored = StoredEvidenceCard(**{**_approved_card_dict(), "status": "rejected"})

    with pytest.raises(ValueError, match="not approved"):
        stored.to_online_card()


def test_evidence_context_round_trip_with_retrieval_trace() -> None:
    context = EvidenceContext(
        cards=[EvidenceCard.from_runtime_dict(_approved_card_dict())],
        card_ids=["card_1"],
        query_summary={"city": "成都", "duration": 3},
        retrieval_trace=RetrievalTrace(
            vector_ranked_ids=["card_1"],
            bm25_ranked_ids=["card_1"],
            fused_ids=["card_1"],
            filters={"city": "成都", "status": "approved"},
        ),
    )

    restored = EvidenceContext.from_runtime_dict(context.to_runtime_dict())

    assert restored.card_ids == ["card_1"]
    assert restored.retrieval_trace.fused_ids == ["card_1"]
    assert restored.query_summary["city"] == "成都"


def test_sufficiency_result_round_trip() -> None:
    result = SufficiencyResult(
        is_sufficient=False,
        score=0.58,
        missing_tags=["熊猫基地"],
        missing_evidence_types=["time_intensity"],
    )

    restored = SufficiencyResult.from_runtime_dict(result.to_runtime_dict())

    assert restored.is_sufficient is False
    assert restored.suggested_action == "mark_assumptions_and_continue"


def test_sufficiency_result_rejects_non_v1_suggested_action() -> None:
    with pytest.raises(ValidationError, match="mark_assumptions_and_continue"):
        SufficiencyResult(
            is_sufficient=False,
            score=0.2,
            suggested_action="external_search",  # type: ignore[arg-type]
        )
