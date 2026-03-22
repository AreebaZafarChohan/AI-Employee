from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.task import Task
from app.models.activity_log import ActivityLog

VALID_STATUS_TRANSITIONS: dict[str, list[str]] = {
    "Pending": ["In Progress", "Done", "Cancelled"],
    "In Progress": ["Done", "Pending", "Cancelled"],
    "Done": [],
    "Cancelled": ["Pending"],
    "PENDING": ["RUNNING", "COMPLETED", "FAILED", "SKIPPED"],
    "RUNNING": ["COMPLETED", "FAILED", "PENDING"],
    "COMPLETED": [],
    "FAILED": ["PENDING", "RUNNING"],
    "SKIPPED": ["PENDING"],
}


async def create_task(db: AsyncSession, title: str, description: str | None = None, status: str = "Pending") -> Task:
    task = Task(title=title, description=description, status=status)
    db.add(task)
    await db.flush()
    db.add(ActivityLog(type="task.created", description=f"Task '{title}' created"))
    await db.commit()
    await db.refresh(task)
    return task


async def get_task(db: AsyncSession, task_id: str) -> Task | None:
    return await db.get(Task, task_id)


async def get_tasks(db: AsyncSession, status: str | None = None, page: int = 1, page_size: int = 20):
    q = select(Task)
    cq = select(func.count(Task.id))
    if status:
        q = q.where(Task.status == status)
        cq = cq.where(Task.status == status)
    q = q.order_by(Task.createdAt.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    tasks = list(result.scalars().all())
    total = (await db.execute(cq)).scalar_one()
    return tasks, total


async def update_task(db: AsyncSession, task_id: str, **kwargs) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    for k, v in kwargs.items():
        if hasattr(task, k):
            setattr(task, k, v)
    if kwargs.get("status") == "Done":
        task.completedAt = datetime.utcnow()
    elif "status" in kwargs:
        task.completedAt = None
    db.add(ActivityLog(type="task.updated", description=f"Task '{task.title}' updated"))
    await db.commit()
    await db.refresh(task)
    return task


async def update_task_status(db: AsyncSession, task_id: str, new_status: str) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    valid = VALID_STATUS_TRANSITIONS.get(task.status, [])
    if new_status not in valid:
        raise ValueError(f"Cannot transition from {task.status} to {new_status}. Valid: {valid}")
    task.status = new_status
    task.completedAt = datetime.utcnow() if new_status in ("Done", "COMPLETED") else None
    db.add(ActivityLog(type="task.updated", description=f"Task '{task.title}' status → {new_status}"))
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: str) -> bool:
    task = await db.get(Task, task_id)
    if not task:
        return False
    await db.delete(task)
    db.add(ActivityLog(type="task.deleted", description=f"Task {task_id} deleted"))
    await db.commit()
    return True
