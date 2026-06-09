"""Prepare-base-context stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "prepare_base_context"


class PrepareBaseContextStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "base context skeleton completed"
