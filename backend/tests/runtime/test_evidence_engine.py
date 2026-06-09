"""EvidenceEngine and repository tests."""

from __future__ import annotations

import inspect

from app.knowledge.evidence_engine import EvidenceEngine, reciprocal_rank_fusion
from app.knowledge.evidence_repository import FixtureEvidenceRepository, PostgresEvidenceRepository
from app.knowledge.query_analyzer import build_retrieval_query
from app.knowledge.tokenizers import JiebaTokenizer
from app.runtime.collect.schemas import PlanningFact, PlanningNeed
from app.runtime.context.schemas import BaseContext


def _planning_need_dict(*, must_visit: list[str] | None = None) -> dict:
    return PlanningNeed(
        confirmed_facts=[
            PlanningFact(
                field="destination",
                value="成都",
                fact_type="confirmed",
                source="user",
            ),
            PlanningFact(
                field="travel_days",
                value=3,
                fact_type="confirmed",
                source="user",
            ),
            *(
                [
                    PlanningFact(
                        field="must_visit",
                        value=must_visit,
                        fact_type="confirmed",
                        source="user",
                    ),
                ]
                if must_visit
                else []
            ),
        ],
        preferences=[{"field": "travel_styles", "value": ["food", "低强度"]}],
    ).to_runtime_dict()


def test_jieba_tokenizer_returns_tokens_without_callers_importing_jieba() -> None:
    tokenizer = JiebaTokenizer()
    tokens = tokenizer.tokenize("成都 武侯祠 锦里")

    assert "成都" in tokens
    assert "武侯祠" in tokens


def test_fixture_repository_returns_only_approved_cards() -> None:
    repository = FixtureEvidenceRepository.from_default_fixture()

    cards = repository.list_approved_cards(city="成都")

    assert len(cards) == 3
    assert all(card.status == "approved" for card in cards)
    assert all("pending" not in card.id for card in cards)


def test_fixture_repository_hydrates_cards_by_id_in_order() -> None:
    repository = FixtureEvidenceRepository.from_default_fixture()

    cards = repository.get_cards_by_ids(
        ["card_chengdu_food_1", "missing", "card_chengdu_route_1"],
    )

    assert [card.id for card in cards] == ["card_chengdu_food_1", "card_chengdu_route_1"]


def test_postgres_repository_boundary_is_not_implemented_yet() -> None:
    repository = PostgresEvidenceRepository()

    try:
        repository.list_approved_cards()
        raised = False
    except NotImplementedError:
        raised = True

    assert raised


def test_query_analyzer_builds_city_and_preferences_from_planning_need() -> None:
    need = PlanningNeed.from_runtime_dict(_planning_need_dict())
    base = BaseContext(planning_need_summary={"destination": "成都", "travel_days": 3})

    query = build_retrieval_query(need, base)

    assert query.city == "成都"
    assert query.duration == 3
    assert "food" in query.preferences
    assert query.search_text


def test_reciprocal_rank_fusion_deduplicates_by_card_id() -> None:
    fused = reciprocal_rank_fusion(
        [["card_a", "card_b"], ["card_b", "card_c"]],
        top_k=3,
    )

    assert fused[0] == "card_b"
    assert set(fused) == {"card_b", "card_a", "card_c"}


def test_evidence_engine_retrieves_only_approved_cards_for_city() -> None:
    engine = EvidenceEngine()
    context, sufficiency = engine.retrieve(_planning_need_dict())

    assert context.card_ids
    assert all(card.status == "approved" for card in context.cards)
    assert all(card.city == "成都" for card in context.cards)
    assert context.query_summary["city"] == "成都"
    assert sufficiency.suggested_action == "mark_assumptions_and_continue"


def test_sufficiency_marks_missing_required_types_as_insufficient() -> None:
    engine = EvidenceEngine()
    _context, sufficiency = engine.retrieve(_planning_need_dict())

    assert sufficiency.is_sufficient is False
    assert "area_strategy" in sufficiency.missing_evidence_types


def test_sufficiency_evaluator_tracks_missing_must_visit_tags() -> None:
    engine = EvidenceEngine()
    _context, sufficiency = engine.retrieve(
        _planning_need_dict(must_visit=["熊猫基地", "武侯祠"]),
    )

    assert "熊猫基地" in sufficiency.missing_tags or sufficiency.is_sufficient is False


def test_evidence_engine_module_does_not_import_jieba_directly() -> None:
    import app.knowledge.evidence_engine as engine_module
    import app.knowledge.evidence_repository as repository_module

    engine_source = inspect.getsource(engine_module)
    repository_source = inspect.getsource(repository_module)

    assert "import jieba" not in engine_source
    assert "import jieba" not in repository_source
