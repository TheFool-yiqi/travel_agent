"""Collect stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "collect"


class CollectStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "collect skeleton completed"
