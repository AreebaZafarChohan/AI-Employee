from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.services import plan_service

router = APIRouter(prefix="/plans", tags=["plans"])


class PlanCreate(BaseModel):
    taskId: str
    steps: list[dict] | None = None


class StatusUpdate(BaseModel):
    status: str


def _serialize_step(s):
    return {"id": s.id, "planId": s.planId, "order": s.order, "title": s.title, "description": s.description,
            "estimatedDuration": s.estimatedDuration, "completed": s.completed, "createdAt": s.createdAt.isoformat()}


def _serialize(p):
    return {"id": p.id, "taskId": p.taskId, "status": p.status,
            "createdAt": p.createdAt.isoformat(), "updatedAt": p.updatedAt.isoformat(),
            "steps": [_serialize_step(s) for s in (p.steps or [])]}


@router.get("")
async def list_plans(status: str | None = None, page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    plans, total = await plan_service.get_plans(db, status=status, page=page, page_size=pageSize)
    return {"data": [_serialize(p) for p in plans], "meta": {"total": total, "page": page, "pageSize": pageSize}}


@router.post("", status_code=201)
async def create_plan(body: PlanCreate, db: AsyncSession = Depends(get_db)):
    plan = await plan_service.create_plan(db, task_id=body.taskId, steps=body.steps)
    return {"data": _serialize(plan)}


@router.get("/{plan_id}")
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    plan = await plan_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Plan not found"})
    return {"data": _serialize(plan)}


@router.patch("/{plan_id}/status")
async def update_status(plan_id: str, body: StatusUpdate, db: AsyncSession = Depends(get_db)):
    plan = await plan_service.update_plan_status(db, plan_id, body.status)
    if not plan:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Plan not found"})
    return {"data": _serialize(plan)}


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    deleted = await plan_service.delete_plan(db, plan_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Plan not found"})
