from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.models.base import get_db
from src.models.pipeline_stage import PipelineStage
from src.models.user import User
from src.models.enums import PipelineStageStatus, UserRole
from src.middleware.auth import require_role

router = APIRouter()


@router.get("/analytics/retries")
async def get_retry_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.APPROVER)),
):
    total_stages = db.query(func.count(PipelineStage.id)).scalar() or 0
    retried = db.query(func.count(PipelineStage.id)).filter(PipelineStage.retry_count > 0).scalar() or 0
    failed = db.query(func.count(PipelineStage.id)).filter(PipelineStage.status == PipelineStageStatus.FAILED).scalar() or 0
    return {
        "total_stages": total_stages,
        "retried_stages": retried,
        "failed_stages": failed,
        "retry_rate": round(retried / total_stages * 100, 2) if total_stages > 0 else 0,
    }
