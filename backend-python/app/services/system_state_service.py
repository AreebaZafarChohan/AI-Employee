from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_state import SystemState
from app.models.activity_log import ActivityLog

SINGLETON_ID = "system-state-singleton"

STATE_TRANSITIONS: dict[str, list[str]] = {
    "Idle": ["Thinking", "Planning", "Executing"],
    "Thinking": ["Planning", "Idle"],
    "Planning": ["Executing", "Idle"],
    "Executing": ["Idle", "Thinking"],
}


async def get_state(db: AsyncSession) -> SystemState:
    state = await db.get(SystemState, SINGLETON_ID)
    if not state:
        state = SystemState(id=SINGLETON_ID, state="Idle", lastActivity=datetime.utcnow())
        db.add(state)
        await db.commit()
        await db.refresh(state)
    return state


async def set_state(db: AsyncSession, new_state: str) -> SystemState:
    current = await get_state(db)
    valid = STATE_TRANSITIONS.get(current.state, [])
    if new_state not in valid:
        raise ValueError(f"Cannot transition from {current.state} to {new_state}. Valid: {valid}")
    current.state = new_state
    current.lastActivity = datetime.utcnow()
    db.add(ActivityLog(type="state.changed", description=f"System state → {new_state}"))
    await db.commit()
    await db.refresh(current)
    return current


async def get_health(db: AsyncSession) -> dict:
    try:
        from sqlalchemy import text
        await db.execute(text("SELECT 1"))
        db_status = "up"
    except Exception:
        db_status = "down"
    return {
        "status": "healthy" if db_status == "up" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {"database": db_status},
    }
