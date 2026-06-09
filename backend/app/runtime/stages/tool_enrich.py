"""Tool-enrich stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "tool_enrich"


class ToolEnrichStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "tool enrichment skeleton completed"
