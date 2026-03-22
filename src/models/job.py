from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, ENUM as PostgreSQLEnum
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin, TimestampMixin


class Job(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "jobs"

    task_description = Column(Text, nullable=False)
    status = Column(PostgreSQLEnum(
        'queued', 'processing', 'completed', 'failed', 'pending_approval',
        name='job_status', create_type=False
    ), nullable=False, default='queued', index=True)
    progress_percentage = Column(Integer, default=0)
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    submitted_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    parent_job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=True, index=True)

    stages = relationship("PipelineStage", back_populates="job", order_by="PipelineStage.started_at")
    plan = relationship("Plan", back_populates="job", uselist=False)
