"""Retrieve-evidence stage skeleton."""

from app.runtime.stages.base import SkeletonStageHandler

STAGE_NAME = "retrieve_evidence"


class RetrieveEvidenceStageHandler(SkeletonStageHandler):
    stage_name = STAGE_NAME
    summary = "evidence retrieval skeleton completed"
