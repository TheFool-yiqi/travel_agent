"""Quality schema contract tests."""

from __future__ import annotations

from app.runtime.quality.schemas import QualityIssue, QualityReport


def test_quality_report_round_trip() -> None:
    report = QualityReport(
        is_acceptable=False,
        has_blocking_issues=True,
        score=0.6,
        issues=[
            QualityIssue(
                code="assumptions_missing",
                message="缺少 assumptions",
                severity="blocking",
            ),
        ],
        unsupported_claims=["故宫"],
        suggested_action="surface_to_user",
    )
    restored = QualityReport.from_runtime_dict(report.to_runtime_dict())
    assert restored == report
