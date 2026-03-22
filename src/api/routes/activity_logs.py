"""Activity logs router."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
from src.models.sqlite_db import get_db
from src.models.dashboard_models import ActivityLog
from src.api.response import api_response

router = APIRouter(prefix="/activity-logs", tags=["Activity Logs"])


class CreateActivityInput(BaseModel):
    type: str
    description: str
    metadata: Optional[str] = None


@router.get("")
async def list_activity_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.timestamp.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    total = db.query(ActivityLog).count()
    return api_response(
        [l.to_dict() for l in logs],
        meta={"total": total, "limit": limit, "offset": offset},
    )


@router.post("")
async def create_activity_log(body: CreateActivityInput, db: Session = Depends(get_db)):
    log = ActivityLog(type=body.type, description=body.description, extra_metadata=body.metadata)
    db.add(log)
    db.commit()
    db.refresh(log)
    return api_response(log.to_dict())
