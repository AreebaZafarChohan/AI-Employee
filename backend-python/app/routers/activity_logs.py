from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services import activity_log_service

router = APIRouter(prefix="/activity-logs", tags=["activity-logs"])


class LogCreate(BaseModel):
    type: str
    description: str
    metadata: str | None = None


def _serialize(log):
    return {"id": log.id, "type": log.type, "description": log.description,
            "timestamp": log.timestamp.isoformat(), "metadata": log.extra_metadata}


@router.get("")
async def list_logs(page: int = Query(1, ge=1), pageSize: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db)):
    logs, total = await activity_log_service.get_activity_logs(db, page=page, page_size=pageSize)
    return {"data": [_serialize(l) for l in logs], "meta": {"total": total, "page": page, "pageSize": pageSize}}


@router.post("", status_code=201)
async def create_log(body: LogCreate, db: AsyncSession = Depends(get_db)):
    log = await activity_log_service.create_activity_log(db, type_=body.type, description=body.description, metadata=body.metadata)
    return {"data": _serialize(log)}
