"""Frozen PlanningRuntime V1 stage manifest."""

V1_STAGE_NAMES: tuple[str, ...] = (
    "collect",
    "prepare_base_context",
    "retrieve_evidence",
    "tool_enrich",
    "domain_plan",
    "integrate",
    "verify",
    "approve_or_revise",
    "finalize",
)


def is_valid_stage(stage: str) -> bool:
    """Return whether a stage belongs to the frozen V1 runtime flow."""
    return stage in V1_STAGE_NAMES
