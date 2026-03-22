from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from src.models.base import get_db
from src.models.user import User
from src.models.enums import JobStatus
from src.middleware.auth import get_current_user
from src.services.job_service import JobService
from src.services.idempotency_service import IdempotencyService
from src.services.audit_service import AuditService
from src.schemas.job import JobSubmission, JobQueuedResponse, JobDetail, JobListResponse, JobSummary
from src.schemas.history import JobHistory, PipelineStageDetail, AgentLogDetail, ApprovalEventDetail
from src.events.event_bus import publish_event
from src.events.types import EventType

router = APIRouter()


@router.post("/jobs", response_model=JobQueuedResponse, status_code=201)
async def submit_job(
    payload: JobSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        idem_service = IdempotencyService()
        existing = idem_service.check_and_set(str(current_user.id), payload.task_description)
        if existing:
            job = JobService(db).get_job(UUID(existing))
            return JobQueuedResponse(job_id=job.id, status=job.status, submitted_at=job.submitted_at)
    except Exception:
        pass  # Redis unavailable, skip idempotency

    svc = JobService(db)
    job = svc.create_job(payload.task_description, current_user.id)

    try:
        IdempotencyService().set(str(current_user.id), payload.task_description, str(job.id))
    except Exception:
        pass

    publish_event(EventType.JOB_QUEUED, {"job_id": str(job.id), "user_id": str(current_user.id)})
    return JobQueuedResponse(job_id=job.id, status=job.status, submitted_at=job.submitted_at)


@router.get("/jobs/{job_id}", response_model=JobDetail)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = JobService(db).get_job(job_id)
    if job.submitted_by != current_user.id and current_user.role.value != "approver":
        raise HTTPException(status_code=403, detail="Not authorized")
    return JobDetail.model_validate(job)


@router.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    svc = JobService(db)
    items, total = svc.list_jobs(current_user.id, status=status, page=page, page_size=page_size)
    return JobListResponse(
        items=[JobSummary.model_validate(j) for j in items],
        total=total, page=page, page_size=page_size,
    )


@router.get("/jobs/{job_id}/history", response_model=JobHistory)
async def get_job_history(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    audit = AuditService(db)
    data = audit.get_job_history(job_id)
    job = data["job"]
    if job.submitted_by != current_user.id and current_user.role.value != "approver":
        raise HTTPException(status_code=403, detail="Not authorized")
    return JobHistory(
        id=job.id, task_description=job.task_description, status=job.status,
        progress_percentage=job.progress_percentage, submitted_at=job.submitted_at,
        completed_at=job.completed_at, parent_job_id=job.parent_job_id,
        stages=[PipelineStageDetail.model_validate(s) for s in data["stages"]],
        agent_logs=[AgentLogDetail.model_validate(a) for a in data["agent_logs"]],
        approval_events=[ApprovalEventDetail.model_validate(e) for e in data["approval_events"]],
    )
