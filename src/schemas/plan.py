from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from src.models.enums import ApprovalStatus, ApprovalDecision


class PlanDetail(BaseModel):
    id: UUID
    job_id: UUID
    version: int
    task_analysis: dict | None = None
    recommended_actions: dict | None = None
    risk_assessment: dict | None = None
    approval_status: ApprovalStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalRequest(BaseModel):
    comments: str | None = None


class ApprovalResponse(BaseModel):
    plan_id: UUID
    decision: ApprovalDecision
    decided_at: datetime


class RejectionRequest(BaseModel):
    comments: str = Field(..., min_length=1, max_length=5000)


class RejectionResponse(BaseModel):
    plan_id: UUID
    decision: ApprovalDecision
    regeneration_job_id: UUID | None = None
    decided_at: datetime
