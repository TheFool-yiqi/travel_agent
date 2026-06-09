"""EvidenceCard repository boundary."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Protocol, runtime_checkable

from app.knowledge.evidence_schemas import EvidenceCard, StoredEvidenceCard


@runtime_checkable
class EvidenceRepository(Protocol):
    def list_approved_cards(self, *, city: str | None = None) -> list[EvidenceCard]:
        ...

    def get_cards_by_ids(self, card_ids: list[str]) -> list[EvidenceCard]:
        ...


class FixtureEvidenceRepository:
    """Load approved EvidenceCards from local JSON fixtures."""

    def __init__(self, fixture_path: Path) -> None:
        self._fixture_path = fixture_path
        self._stored_cards = self._load_stored_cards(fixture_path)
        self._approved_by_id = {
            card.id: card
            for stored in self._stored_cards
            if stored.status == "approved"
            for card in [stored.to_online_card()]
        }

    @classmethod
    def from_default_fixture(cls) -> FixtureEvidenceRepository:
        root = Path(__file__).resolve().parents[2]
        fixture_path = root / "tests" / "fixtures" / "evidence" / "approved_chengdu_cards.json"
        return cls(fixture_path)

    def list_approved_cards(self, *, city: str | None = None) -> list[EvidenceCard]:
        cards = list(self._approved_by_id.values())
        if city is None:
            return cards
        return [card for card in cards if card.city == city]

    def get_cards_by_ids(self, card_ids: list[str]) -> list[EvidenceCard]:
        results: list[EvidenceCard] = []
        for card_id in card_ids:
            card = self._approved_by_id.get(card_id)
            if card is not None:
                results.append(card)
        return results

    @staticmethod
    def _load_stored_cards(fixture_path: Path) -> list[StoredEvidenceCard]:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list):
            raise ValueError(f"Evidence fixture must be a list: {fixture_path}")
        return [StoredEvidenceCard.model_validate(item) for item in payload]


class PostgresEvidenceRepository:
    """Reserved PG-backed repository; not implemented in Slice 4 Task 3."""

    def list_approved_cards(self, *, city: str | None = None) -> list[EvidenceCard]:
        raise NotImplementedError("PostgresEvidenceRepository is not implemented in V1 Slice 4")

    def get_cards_by_ids(self, card_ids: list[str]) -> list[EvidenceCard]:
        raise NotImplementedError("PostgresEvidenceRepository is not implemented in V1 Slice 4")
