"""Single-pass revision agent for verify stage."""

from __future__ import annotations

from app.runtime.planning.schemas import ItineraryDraft
from app.runtime.quality.schemas import QualityReport
from app.runtime.state import RuntimeState


class RevisionAgent:
    """Apply one deterministic auto-revision pass before re-verification."""

    def revise(self, state: RuntimeState, report: QualityReport) -> ItineraryDraft:
        draft = _load_draft(state)
        return self._revise_from_quality_report(draft, state, report)

    def revise_from_user_feedback(self, state: RuntimeState, feedback: str) -> ItineraryDraft:
        """Apply a deterministic revision pass from explicit user feedback."""
        draft = _load_draft(state)
        note = f"用户修订意见：{feedback.strip()}"
        if note not in draft.integration_notes:
            draft.integration_notes.append(note)

        summary = draft.summary.strip()
        suffix = "（已按用户意见修订）"
        draft.summary = f"{summary}{suffix}" if summary else suffix.lstrip("（").rstrip("）")

        if draft.days:
            days = [dict(day) for day in draft.days]
            first_day = days[0]
            activities = list(first_day.get("activities") or [])
            marker = "按用户偏好调整后的体验"
            if marker not in activities:
                activities.append(marker)
            first_day["activities"] = activities
            days[0] = first_day
            draft.days = days

        return draft

    def _revise_from_quality_report(
        self,
        draft: ItineraryDraft,
        state: RuntimeState,
        report: QualityReport,
    ) -> ItineraryDraft:
        issue_codes = {issue.code for issue in report.issues}

        if "assumptions_missing" in issue_codes or "evidence_insufficient" in issue_codes:
            sufficiency = state.get("sufficiency_result") or {}
            missing_types = sufficiency.get("missing_evidence_types") or []
            assumption = (
                "证据不足，以下安排含假设"
                if not missing_types
                else f"证据类型 {', '.join(missing_types)} 未覆盖，以下安排含假设"
            )
            if assumption not in draft.assumptions:
                draft.assumptions.append(assumption)

        if "day_count_mismatch" in issue_codes:
            draft.days = _normalize_day_count(draft.days, draft.travel_days, draft.destination)

        weather = ((state.get("tool_context") or {}).get("weather") or {})
        for risk in weather.get("risks") or []:
            note = f"天气提示：{risk}"
            if note not in draft.integration_notes:
                draft.integration_notes.append(note)

        for issue in report.issues:
            if issue.code == "unsupported_claim":
                note = f"待核实：{issue.message}"
                if note not in draft.integration_notes:
                    draft.integration_notes.append(note)

        return draft


def _load_draft(state: RuntimeState) -> ItineraryDraft:
    draft_raw = state.get("itinerary_draft")
    if not draft_raw:
        raise ValueError("RevisionAgent requires itinerary_draft")
    return ItineraryDraft.from_runtime_dict(dict(draft_raw))


def _normalize_day_count(
    days: list[dict],
    travel_days: int,
    destination: str,
) -> list[dict]:
    normalized = [dict(day) for day in days]
    while len(normalized) < travel_days:
        day_number = len(normalized) + 1
        normalized.append(
            {
                "day_number": day_number,
                "theme": f"第{day_number}天",
                "activities": [f"{destination} 机动安排"],
                "meals": {"lunch": "就近简餐", "dinner": f"{destination} 本地餐饮"},
                "accommodation": f"{destination} 交通便利区域",
                "plan_b": "如遇天气不佳，改为室内体验",
            },
        )
    if len(normalized) > travel_days:
        normalized = normalized[:travel_days]
    for index, day in enumerate(normalized, start=1):
        day["day_number"] = index
    return normalized
