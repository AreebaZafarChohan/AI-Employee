from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from src.models.base import get_db
from src.models.user import User
from src.middleware.auth import get_current_user
from src.services.plan_service import PlanService
from src.schemas.plan import PlanDetail

router = APIRouter()


@router.get("/plans/{plan_id}", response_model=PlanDetail)
async def get_plan(
    plan_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = PlanService(db).get_plan(plan_id)
    return PlanDetail.model_validate(plan)
