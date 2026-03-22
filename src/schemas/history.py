from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from src.models.enums import (
    JobStatus, PipelineStageType, PipelineStageStatus,
    ApprovalDecision, AgentType, AgentExecutionStatus
)


class PipelineStageDetail(BaseModel):
    id: UUID
    stage_type: PipelineStageType
    status: PipelineStageStatus
    input_data: dict | None = None
    output_data: dict | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
    retry_count: int

    model_config = {"from_attributes": True}


class AgentLogDetail(BaseModel):
    id: UUID
    agent_type: AgentType
    status: AgentExecutionStatus
    duration_ms: int | None = None
    executed_at: datetime

    model_config = {"from_attributes": True}


class ApprovalEventDetail(BaseModel):
    id: UUID
    decision: ApprovalDecision
    approver_id: UUID
    decided_at: datetime
    comments: str | None = None

    model_config = {"from_attributes": True}


class JobHistory(BaseModel):
    id: UUID
    task_description: str
    status: JobStatus
    progress_percentage: int
    submitted_at: datetime
    completed_at: datetime | None = None
    parent_job_id: UUID | None = None
    stages: list[PipelineStageDetail]
    agent_logs: list[AgentLogDetail]
    approval_events: list[ApprovalEventDetail]
