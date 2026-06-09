"""Evidence sufficiency evaluation for PlanningRuntime."""

from __future__ import annotations

from app.knowledge.evidence_schemas import EvidenceCard, SufficiencyResult
from app.knowledge.query_analyzer import RetrievalQuery

SUFFICIENCY_THRESHOLD = 0.75


def evaluate_sufficiency(query: RetrievalQuery, cards: list[EvidenceCard]) -> SufficiencyResult:
    """Evaluate whether retrieved approved cards cover planning needs."""
    if not query.required_evidence_types:
        return SufficiencyResult(is_sufficient=True, score=1.0)

    present_types = {card.evidence_type for card in cards}
    missing_evidence_types = [
        evidence_type
        for evidence_type in query.required_evidence_types
        if evidence_type not in present_types
    ]
    type_coverage = 1.0 - (
        len(missing_evidence_types) / len(query.required_evidence_types)
    )

    missing_tags: list[str] = []
    if query.must_visit:
        searchable_text = " ".join(
            [
                *(card.claim for card in cards),
                *(entity for card in cards for entity in card.entities),
                *(tag for card in cards for tag in card.applies_to),
            ],
        )
        for tag in query.must_visit:
            if tag not in searchable_text:
                missing_tags.append(tag)
        tag_coverage = 1.0 - (len(missing_tags) / len(query.must_visit))
    else:
        tag_coverage = 1.0

    score = round((type_coverage + tag_coverage) / 2, 2)
    is_sufficient = score >= SUFFICIENCY_THRESHOLD and not missing_evidence_types

    return SufficiencyResult(
        is_sufficient=is_sufficient,
        score=score,
        missing_tags=missing_tags,
        missing_evidence_types=missing_evidence_types,
        suggested_action="mark_assumptions_and_continue",
    )
