from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.plan import Plan
from app.models.plan_step import PlanStep
from app.models.activity_log import ActivityLog


async def create_plan(db: AsyncSession, task_id: str, steps: list[dict] | None = None) -> Plan:
    plan = Plan(taskId=task_id, status="Draft")
    db.add(plan)
    await db.flush()
    if steps:
        for i, s in enumerate(steps):
            db.add(PlanStep(planId=plan.id, order=i + 1, title=s["title"], description=s["description"],
                            estimatedDuration=s.get("estimatedDuration")))
    db.add(ActivityLog(type="plan.created", description=f"Plan created for task {task_id}"))
    await db.commit()
    return await get_plan(db, plan.id)  # type: ignore


async def get_plan(db: AsyncSession, plan_id: str) -> Plan | None:
    q = select(Plan).options(selectinload(Plan.steps)).where(Plan.id == plan_id)
    result = await db.execute(q)
    return result.scalar_one_or_none()


async def get_plans(db: AsyncSession, status: str | None = None, page: int = 1, page_size: int = 20):
    q = select(Plan).options(selectinload(Plan.steps))
    cq = select(func.count(Plan.id))
    if status:
        q = q.where(Plan.status == status)
        cq = cq.where(Plan.status == status)
    q = q.order_by(Plan.createdAt.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    plans = list(result.scalars().unique().all())
    total = (await db.execute(cq)).scalar_one()
    return plans, total


async def update_plan_status(db: AsyncSession, plan_id: str, new_status: str) -> Plan | None:
    plan = await get_plan(db, plan_id)
    if not plan:
        return None
    plan.status = new_status
    db.add(ActivityLog(type="plan.updated", description=f"Plan {plan_id} status → {new_status}"))
    await db.commit()
    await db.refresh(plan)
    return plan


async def delete_plan(db: AsyncSession, plan_id: str) -> bool:
    plan = await db.get(Plan, plan_id)
    if not plan:
        return False
    await db.delete(plan)
    db.add(ActivityLog(type="plan.deleted", description=f"Plan {plan_id} deleted"))
    await db.commit()
    return True
