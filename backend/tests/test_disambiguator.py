"""disambiguator 测试（P2.2）"""

from app.graph.semantic.disambiguator import (
    ambiguity_to_pending,
    apply_budget_scope_resolution,
    detect_ambiguities,
)


def test_budget_unknown_scope_ambiguity():
    amb = detect_ambiguities(
        {"budget_scope": "unknown", "budget_amount": 5000},
        {},
        guidance_step="budget",
    )
    assert amb
    assert amb[0].kind == "budget_scope"
    assert "每人" in amb[0].question


def test_budget_total_without_party():
    amb = detect_ambiguities(
        {"budget_scope": "total", "budget_amount": 8000},
        {"adult_count": None},
        guidance_step="budget",
    )
    assert amb
    assert "人数" in amb[0].question


def test_apply_budget_per_person():
    pending = {"budget_amount": 5000, "budget_scope": "unknown"}
    result = apply_budget_scope_resolution({}, pending, "每人")
    assert result
    assert result["budget_min"] < 5000
    assert result["budget_max"] > 5000


def test_apply_budget_total_with_party():
    pending = {"budget_amount": 6000, "budget_scope": "total"}
    fields = {"adult_count": 2, "children_count": 0, "party_confirmed": True}
    result = apply_budget_scope_resolution(fields, pending, "总共")
    assert result
    assert result["budget_max"] <= 3500


def test_ambiguity_to_pending():
    from app.graph.semantic.disambiguator import Ambiguity

    pending = ambiguity_to_pending(
        Ambiguity(
            kind="budget_scope",
            slot="budget",
            question="test?",
            context={"budget_amount": 1000},
        ),
    )
    assert pending["budget_amount"] == 1000
