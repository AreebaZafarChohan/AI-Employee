from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.task import Task
from app.models.goal import Goal
from app.models.cost_log import CostLog

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics(db: AsyncSession = Depends(get_db)):
    tasks_total = (await db.execute(select(func.count(Task.id)))).scalar_one()
    tasks_done = (await db.execute(select(func.count(Task.id)).where(Task.status.in_(["Done", "COMPLETED"])))).scalar_one()
    goals_total = (await db.execute(select(func.count(Goal.id)))).scalar_one()
    total_cost = (await db.execute(select(func.sum(CostLog.estimatedCostUsd)))).scalar_one_or_none() or 0
    return {"data": {
        "tasks": {"total": tasks_total, "completed": tasks_done},
        "goals": {"total": goals_total},
        "costs": {"totalUsd": str(total_cost)},
    }}
