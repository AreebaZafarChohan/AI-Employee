from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from src.models.enums import JobStatus


class JobSubmission(BaseModel):
    task_description: str = Field(..., min_length=10, max_length=10000)


class JobQueuedResponse(BaseModel):
    job_id: UUID
    status: JobStatus
    submitted_at: datetime


class JobDetail(BaseModel):
    id: UUID
    task_description: str
    status: JobStatus
    progress_percentage: int
    submitted_by: UUID
    submitted_at: datetime
    completed_at: datetime | None = None
    parent_job_id: UUID | None = None

    model_config = {"from_attributes": True}


class JobSummary(BaseModel):
    id: UUID
    status: JobStatus
    progress_percentage: int
    submitted_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    items: list[JobSummary]
    total: int
    page: int
    page_size: int
