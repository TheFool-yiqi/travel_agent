"""Deterministic quality verifier for PlanningRuntime V1."""

from __future__ import annotations

from datetime import UTC, datetime

from app.runtime.planning.schemas import ItineraryDraft
from app.runtime.quality.schemas import QualityIssue, QualityReport
from app.runtime.state import RuntimeState

_KNOWN_OUT_OF_SCOPE_POIS = ("故宫", "外滩", "西湖")


class QualityVerifier:
    """Rule-based judge over itinerary draft and structured runtime context."""

    def verify(self, state: RuntimeState) -> QualityReport:
        issues: list[QualityIssue] = []
        unsupported_claims: list[str] = []

        draft_raw = state.get("itinerary_draft")
        if not draft_raw:
            return self._report_from_issues(
                [
                    QualityIssue(
                        code="missing_itinerary_draft",
                        message="缺少 itinerary_draft，无法验证",
                        severity="blocking",
                    ),
                ],
                unsupported_claims=[],
            )

        draft = ItineraryDraft.from_runtime_dict(draft_raw)
        if len(draft.days) != draft.travel_days:
            issues.append(
                QualityIssue(
                    code="day_count_mismatch",
                    message=(
                        f"行程天数不一致：travel_days={draft.travel_days}，"
                        f"days={len(draft.days)}"
                    ),
                    severity="blocking",
                    field="itinerary_draft.days",
                ),
            )

        if not draft.summary.strip():
            issues.append(
                QualityIssue(
                    code="empty_summary",
                    message="行程草案缺少 summary",
                    severity="warning",
                    field="itinerary_draft.summary",
                ),
            )

        sufficiency = state.get("sufficiency_result") or {}
        if sufficiency.get("is_sufficient") is False and not draft.assumptions:
            issues.append(
                QualityIssue(
                    code="assumptions_missing",
                    message="证据不足但未在草案中标记 assumptions",
                    severity="blocking",
                    field="itinerary_draft.assumptions",
                ),
            )
        elif sufficiency.get("is_sufficient") is False:
            issues.append(
                QualityIssue(
                    code="evidence_insufficient",
                    message="证据覆盖不足，需严格检查假设项",
                    severity="warning",
                ),
            )

        allowed_terms = _collect_allowed_terms(state, draft)
        unsupported_claims = _find_unsupported_claims(draft, allowed_terms)
        for claim in unsupported_claims:
            issues.append(
                QualityIssue(
                    code="unsupported_claim",
                    message=f"草案包含未证据支持的表述：{claim}",
                    severity="warning",
                    field="itinerary_draft.days",
                ),
            )

        weather = ((state.get("tool_context") or {}).get("weather") or {})
        weather_risks = weather.get("risks") or []
        if weather.get("status") == "available" and weather_risks:
            draft_text = draft.model_dump_json()
            if not any(token in draft_text for token in ("天气", "雨", "weather")):
                issues.append(
                    QualityIssue(
                        code="weather_risk_not_reflected",
                        message="天气风险未反映到行程草案",
                        severity="warning",
                    ),
                )

        return self._report_from_issues(issues, unsupported_claims=unsupported_claims)

    @staticmethod
    def _report_from_issues(
        issues: list[QualityIssue],
        *,
        unsupported_claims: list[str],
        revision_applied: bool = False,
    ) -> QualityReport:
        blocking = [issue for issue in issues if issue.severity == "blocking"]
        warnings = [issue for issue in issues if issue.severity == "warning"]
        score = max(
            0.0,
            round(1.0 - 0.25 * len(blocking) - 0.05 * len(warnings), 2),
        )
        has_blocking = bool(blocking)
        is_acceptable = not has_blocking and not unsupported_claims
        suggested_action: str = "continue"
        if has_blocking or unsupported_claims:
            suggested_action = "surface_to_user"

        return QualityReport(
            is_acceptable=is_acceptable,
            has_blocking_issues=has_blocking,
            score=score,
            issues=issues,
            unsupported_claims=unsupported_claims,
            revision_applied=revision_applied,
            suggested_action=suggested_action,
            verified_at=datetime.now(UTC).isoformat(),
        )


def _collect_allowed_terms(state: RuntimeState, draft: ItineraryDraft) -> set[str]:
    terms = {draft.destination, "机动", "休息", "简餐", "餐饮", "交通", "区域", "游览", "体验"}
    for card in (state.get("evidence_context") or {}).get("cards") or []:
        if not isinstance(card, dict):
            continue
        terms.add(str(card.get("claim") or ""))
        for entity in card.get("entities") or []:
            terms.add(str(entity))
    for assumption in draft.assumptions:
        terms.add(str(assumption))
    return {term.strip() for term in terms if str(term).strip()}


def _find_unsupported_claims(
    draft: ItineraryDraft,
    allowed_terms: set[str],
) -> list[str]:
    unsupported: list[str] = []
    serialized_allowed = " ".join(allowed_terms)

    for poi in _KNOWN_OUT_OF_SCOPE_POIS:
        if poi in draft.model_dump_json() and poi not in serialized_allowed:
            unsupported.append(poi)

    for day in draft.days:
        for activity in day.get("activities") or []:
            text = str(activity)
            for poi in _KNOWN_OUT_OF_SCOPE_POIS:
                if poi in text and poi not in serialized_allowed:
                    unsupported.append(poi)

    return list(dict.fromkeys(unsupported))
