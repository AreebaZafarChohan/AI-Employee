import logging
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.models.pipeline_stage import PipelineStage
from src.models.enums import PipelineStageType, PipelineStageStatus, JobStatus
from src.services.job_service import JobService
from src.events.event_bus import publish_event
from src.events.types import EventType

logger = logging.getLogger("gold_tier")

STAGE_ORDER = [
    PipelineStageType.TASK_ANALYSIS,
    PipelineStageType.PLAN_CREATION,
    PipelineStageType.RISK_ASSESSMENT,
    PipelineStageType.FINAL_OUTPUT,
]


class PipelineService:
    def __init__(self, db: Session):
        self.db = db
        self.job_service = JobService(db)

    def start_pipeline(self, job_id: UUID):
        first_stage = PipelineStage(
            job_id=job_id,
            stage_type=STAGE_ORDER[0],
            status=PipelineStageStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(first_stage)
        self.job_service.update_status(job_id, JobStatus.PROCESSING, progress=0)
        self.db.commit()
        publish_event(EventType.STAGE_STARTED, {"job_id": str(job_id), "stage_type": STAGE_ORDER[0].value})
        return first_stage

    def complete_stage(self, stage_id: UUID, output_data: dict):
        stage = self.db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()
        stage.status = PipelineStageStatus.COMPLETED
        stage.output_data = output_data
        stage.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        current_idx = STAGE_ORDER.index(stage.stage_type)
        progress = int(((current_idx + 1) / len(STAGE_ORDER)) * 100)
        self.job_service.update_status(stage.job_id, JobStatus.PROCESSING, progress=progress)

        publish_event(EventType.STAGE_COMPLETED, {
            "job_id": str(stage.job_id), "stage_type": stage.stage_type.value,
            "stage_id": str(stage_id), "progress": progress,
        })

        if current_idx + 1 < len(STAGE_ORDER):
            return self._trigger_next_stage(stage.job_id, current_idx + 1)
        else:
            self.job_service.update_status(stage.job_id, JobStatus.COMPLETED, progress=100)
            publish_event(EventType.JOB_COMPLETED, {"job_id": str(stage.job_id)})
            return None

    def _trigger_next_stage(self, job_id: UUID, stage_idx: int) -> PipelineStage:
        next_stage = PipelineStage(
            job_id=job_id,
            stage_type=STAGE_ORDER[stage_idx],
            status=PipelineStageStatus.RUNNING,
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(next_stage)
        self.db.commit()
        publish_event(EventType.STAGE_STARTED, {"job_id": str(job_id), "stage_type": STAGE_ORDER[stage_idx].value})
        return next_stage

    def handle_stage_failure(self, stage_id: UUID, error_message: str):
        stage = self.db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()
        stage.retry_count += 1
        if stage.retry_count >= 3:
            stage.status = PipelineStageStatus.FAILED
            stage.error_message = error_message
            self.job_service.update_status(stage.job_id, JobStatus.FAILED)
            publish_event(EventType.JOB_FAILED, {"job_id": str(stage.job_id), "error": error_message})
        else:
            stage.status = PipelineStageStatus.RETRYING
            stage.error_message = error_message
            publish_event(EventType.STAGE_FAILED, {
                "job_id": str(stage.job_id), "stage_type": stage.stage_type.value,
                "retry_count": stage.retry_count, "error": error_message,
            })
        self.db.commit()
