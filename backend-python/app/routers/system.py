from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services import system_state_service
from pydantic import BaseModel

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/state")
async def get_state(db: AsyncSession = Depends(get_db)):
    state = await system_state_service.get_state(db)
    return {"data": {"id": state.id, "state": state.state, "lastActivity": state.lastActivity.isoformat(), "updatedAt": state.updatedAt.isoformat() if state.updatedAt else None}}


class StateUpdate(BaseModel):
    state: str


@router.put("/state")
async def set_state(body: StateUpdate, db: AsyncSession = Depends(get_db)):
    try:
        state = await system_state_service.set_state(db, body.state)
        return {"data": {"id": state.id, "state": state.state, "lastActivity": state.lastActivity.isoformat()}}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=409, detail={"code": "INVALID_TRANSITION", "message": str(e)})


@router.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    return {"data": await system_state_service.get_health(db)}
