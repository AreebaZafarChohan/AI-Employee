from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.base import get_db
from src.models.job import Job
from src.models.plan import Plan
from src.models.user import User
from src.models.enums import JobStatus, ApprovalStatus, UserRole
from src.middleware.auth import require_role
from src.schemas.metrics import QueueMetrics

router = APIRouter()


@router.get("/metrics/queue", response_model=QueueMetrics)
async def get_queue_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.APPROVER)),
):
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    queued = db.query(func.count(Job.id)).filter(Job.status == JobStatus.QUEUED).scalar()
    processing = db.query(func.count(Job.id)).filter(Job.status == JobStatus.PROCESSING).scalar()
    completed_today = db.query(func.count(Job.id)).filter(Job.status == JobStatus.COMPLETED, Job.completed_at >= today_start).scalar()
    failed_today = db.query(func.count(Job.id)).filter(Job.status == JobStatus.FAILED, Job.updated_at >= today_start).scalar()
    pending_approval = db.query(func.count(Plan.id)).filter(Plan.approval_status == ApprovalStatus.PENDING_APPROVAL).scalar()

    avg_time = db.query(func.avg(func.extract("epoch", Job.completed_at - Job.submitted_at))).filter(
        Job.status == JobStatus.COMPLETED, Job.completed_at.isnot(None)
    ).scalar()

    return QueueMetrics(
        queued_count=queued or 0, processing_count=processing or 0,
        completed_today=completed_today or 0, failed_today=failed_today or 0,
        avg_completion_time_seconds=float(avg_time) if avg_time else None,
        pending_approval_count=pending_approval or 0,
    )
