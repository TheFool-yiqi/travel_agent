"""歧义检测与澄清问题生成。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

AmbiguityKind = Literal["budget_scope", "city", "budget_amount"]


@dataclass(frozen=True, slots=True)
class Ambiguity:
    kind: AmbiguityKind
    slot: str
    question: str
    options: tuple[str, ...] = ()
    context: dict[str, Any] | None = None


def _render_budget_scope_question(amount: float) -> str:
    amount_text = int(amount) if amount == int(amount) else amount
    return (
        f"您说的 {amount_text} 元是「每人」还是「整趟旅行总共」？"
        "回复「每人」或「总共」就行～"
    )


def detect_ambiguities(
    slot_updates: dict[str, Any],
    fields: dict[str, Any],
    *,
    guidance_step: str,
) -> list[Ambiguity]:
    """检测槽位更新中的歧义，需澄清时返回列表。"""
    ambiguities: list[Ambiguity] = []

    if guidance_step == "budget":
        scope = slot_updates.get("budget_scope")
        amount = slot_updates.get("budget_amount")
        if scope == "unknown" and amount is not None:
            ambiguities.append(
                Ambiguity(
                    kind="budget_scope",
                    slot="budget",
                    question=_render_budget_scope_question(float(amount)),
                    options=("每人", "总共"),
                    context={"budget_amount": amount},
                ),
            )
        elif scope == "total" and amount is not None:
            adult = int(fields.get("adult_count") or 0)
            child = int(fields.get("children_count") or 0)
            party_size = adult + child
            if party_size < 1:
                ambiguities.append(
                    Ambiguity(
                        kind="budget_scope",
                        slot="budget",
                        question=(
                            f"您提到总共 {int(amount)} 元——我先确认一下人数，"
                            "方便折算每人预算。一行几位（成人+儿童）？"
                        ),
                        options=(),
                        context={"budget_amount": amount, "budget_scope": "total"},
                    ),
                )

    return ambiguities


def apply_budget_scope_resolution(
    fields: dict[str, Any],
    pending: dict[str, Any],
    user_text: str,
) -> dict[str, Any] | None:
    """用户澄清预算口径后写入 budget_min/max。"""
    amount = pending.get("budget_amount")
    if amount is None:
        return None

    text = user_text.strip()
    scope = pending.get("budget_scope")
    updates: dict[str, Any] = {}

    if scope == "total" and not fields.get("party_confirmed"):
        return None

    per_person = None
    if "每人" in text or "人均" in text:
        per_person = float(amount)
    elif "总共" in text or "合计" in text or scope == "total":
        party = int(fields.get("adult_count") or 1) + int(fields.get("children_count") or 0)
        party = max(party, 1)
        per_person = float(amount) / party
    elif scope == "per_person":
        per_person = float(amount)

    if per_person is None:
        return None

    margin = per_person * 0.15
    updates["budget_min"] = max(0, round(per_person - margin, 2))
    updates["budget_max"] = round(per_person + margin, 2)
    return updates


def ambiguity_to_pending(ambiguity: Ambiguity) -> dict[str, Any]:
    pending = {
        "slot": ambiguity.slot,
        "kind": ambiguity.kind,
        "question": ambiguity.question,
    }
    if ambiguity.context:
        pending.update(ambiguity.context)
    return pending
