from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services import task_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: str | None = None
    status: str = "Pending"


class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: str | None = None


class StatusUpdate(BaseModel):
    status: str


def _serialize(t):
    return {
        "id": t.id, "goalId": t.goalId, "title": t.title, "description": t.description,
        "status": t.status, "order": t.order, "assignedAgent": t.assignedAgent,
        "createdAt": t.createdAt.isoformat(), "updatedAt": t.updatedAt.isoformat(),
        "completedAt": t.completedAt.isoformat() if t.completedAt else None,
    }


@router.get("")
async def list_tasks(status: str | None = None, page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    tasks, total = await task_service.get_tasks(db, status=status, page=page, page_size=pageSize)
    return {"data": [_serialize(t) for t in tasks], "meta": {"total": total, "page": page, "pageSize": pageSize}}


@router.post("", status_code=201)
async def create_task(body: TaskCreate, db: AsyncSession = Depends(get_db)):
    task = await task_service.create_task(db, title=body.title, description=body.description, status=body.status)
    return {"data": _serialize(task)}


@router.get("/{task_id}")
async def get_task(task_id: str, db: AsyncSession = Depends(get_db)):
    task = await task_service.get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Task not found"})
    return {"data": _serialize(task)}


@router.put("/{task_id}")
async def update_task(task_id: str, body: TaskUpdate, db: AsyncSession = Depends(get_db)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    task = await task_service.update_task(db, task_id, **updates)
    if not task:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Task not found"})
    return {"data": _serialize(task)}


@router.patch("/{task_id}/status")
async def update_status(task_id: str, body: StatusUpdate, db: AsyncSession = Depends(get_db)):
    try:
        task = await task_service.update_task_status(db, task_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": str(e)})
    if not task:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Task not found"})
    return {"data": _serialize(task)}


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await task_service.delete_task(db, task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Task not found"})
