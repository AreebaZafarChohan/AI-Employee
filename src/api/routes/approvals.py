from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from src.models.base import get_db
from src.models.user import User
from src.models.enums import UserRole, ApprovalDecision
from src.middleware.auth import get_current_user, require_role
from src.services.approval_service import ApprovalService
from src.schemas.plan import ApprovalRequest, ApprovalResponse, RejectionRequest, RejectionResponse

router = APIRouter()


@router.post("/plans/{plan_id}/approve", response_model=ApprovalResponse)
async def approve_plan(
    plan_id: UUID,
    payload: ApprovalRequest = ApprovalRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.APPROVER)),
):
    svc = ApprovalService(db)
    event = svc.approve_plan(plan_id, current_user.id, payload.comments)
    return ApprovalResponse(plan_id=plan_id, decision=ApprovalDecision.APPROVED, decided_at=event.decided_at)


@router.post("/plans/{plan_id}/reject", response_model=RejectionResponse)
async def reject_plan(
    plan_id: UUID,
    payload: RejectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.APPROVER)),
):
    svc = ApprovalService(db)
    event, regen_id = svc.reject_plan(plan_id, current_user.id, payload.comments)
    return RejectionResponse(
        plan_id=plan_id, decision=ApprovalDecision.REJECTED,
        regeneration_job_id=regen_id, decided_at=event.decided_at,
    )
