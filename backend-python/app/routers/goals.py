from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.models.goal import Goal

router = APIRouter(prefix="/goals", tags=["goals"])


class GoalCreate(BaseModel):
    title: str
    description: str | None = None
    priority: int = 1


class GoalUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    state: str | None = None
    priority: int | None = None


def _s(g):
    return {"id": g.id, "title": g.title, "description": g.description, "state": g.state,
            "priority": g.priority, "createdAt": g.createdAt.isoformat(), "updatedAt": g.updatedAt.isoformat(), "metadata": g.extra_metadata}


@router.get("")
async def list_goals(state: str | None = None, page: int = Query(1, ge=1), pageSize: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)):
    q = select(Goal)
    cq = select(func.count(Goal.id))
    if state:
        q = q.where(Goal.state == state)
        cq = cq.where(Goal.state == state)
    q = q.order_by(Goal.createdAt.desc()).offset((page - 1) * pageSize).limit(pageSize)
    goals = list((await db.execute(q)).scalars().all())
    total = (await db.execute(cq)).scalar_one()
    return {"data": [_s(g) for g in goals], "meta": {"total": total, "page": page, "pageSize": pageSize}}


@router.post("", status_code=201)
async def create_goal(body: GoalCreate, db: AsyncSession = Depends(get_db)):
    g = Goal(title=body.title, description=body.description, priority=body.priority)
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return {"data": _s(g)}


@router.get("/{goal_id}")
async def get_goal(goal_id: str, db: AsyncSession = Depends(get_db)):
    g = await db.get(Goal, goal_id)
    if not g:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Goal not found"})
    return {"data": _s(g)}


@router.put("/{goal_id}")
async def update_goal(goal_id: str, body: GoalUpdate, db: AsyncSession = Depends(get_db)):
    g = await db.get(Goal, goal_id)
    if not g:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Goal not found"})
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(g, k, v)
    await db.commit()
    await db.refresh(g)
    return {"data": _s(g)}


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(goal_id: str, db: AsyncSession = Depends(get_db)):
    g = await db.get(Goal, goal_id)
    if not g:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Goal not found"})
    await db.delete(g)
    await db.commit()
