"""EvidenceEngine and repository tests."""

from __future__ import annotations

import inspect

from app.knowledge.evidence_repository import FixtureEvidenceRepository, PostgresEvidenceRepository
from app.knowledge.tokenizers import JiebaTokenizer


def test_jieba_tokenizer_returns_tokens_without_callers_importing_jieba() -> None:
    tokenizer = JiebaTokenizer()
    tokens = tokenizer.tokenize("成都 武侯祠 锦里")

    assert "成都" in tokens
    assert "武侯祠" in tokens


def test_evidence_engine_module_does_not_import_jieba_directly() -> None:
    import app.knowledge.evidence_repository as repository_module
    import app.knowledge.tokenizers as tokenizers_module

    repository_source = inspect.getsource(repository_module)
    tokenizer_source = inspect.getsource(tokenizers_module)

    assert "import jieba" not in repository_source
    assert "import jieba" in tokenizer_source


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
