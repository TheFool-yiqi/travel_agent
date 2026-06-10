"""Human-readable labels for V1 PlanningRuntime stages."""

from __future__ import annotations

from app.runtime.manifest import V1_STAGE_NAMES

RUNTIME_STAGE_LABELS: dict[str, str] = {
    "collect": "需求收集",
    "prepare_base_context": "准备规划上下文",
    "retrieve_evidence": "检索证据",
    "tool_enrich": "工具补充",
    "domain_plan": "领域规划",
    "integrate": "行程整合",
    "verify": "质量验证",
    "approve_or_revise": "行程确认",
    "finalize": "订单生成",
}


def stage_label(stage: str) -> str:
    """Return the display label for a V1 runtime stage."""
    return RUNTIME_STAGE_LABELS.get(stage, stage)


def assert_labels_cover_manifest() -> None:
    """Ensure every V1 stage has a label (used in tests)."""
    missing = [stage for stage in V1_STAGE_NAMES if stage not in RUNTIME_STAGE_LABELS]
    if missing:
        raise ValueError(f"Missing runtime stage labels: {missing}")
