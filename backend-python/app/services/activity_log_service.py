from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityLog


async def get_activity_logs(db: AsyncSession, page: int = 1, page_size: int = 50):
    q = select(ActivityLog).order_by(ActivityLog.timestamp.desc()).offset((page - 1) * page_size).limit(page_size)
    cq = select(func.count(ActivityLog.id))
    result = await db.execute(q)
    logs = list(result.scalars().all())
    total = (await db.execute(cq)).scalar_one()
    return logs, total


async def create_activity_log(db: AsyncSession, type_: str, description: str, metadata: str | None = None) -> ActivityLog:
    log = ActivityLog(type=type_, description=description, extra_metadata=metadata)
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log
