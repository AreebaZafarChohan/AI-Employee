from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PostgreSQLEnum
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin


class PipelineStage(Base, UUIDMixin):
    __tablename__ = "pipeline_stages"

    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    stage_type = Column(PostgreSQLEnum(
        'task_analysis', 'plan_creation', 'risk_assessment', 'final_output',
        name='pipeline_stage_type', create_type=False
    ), nullable=False, index=True)
    status = Column(PostgreSQLEnum(
        'pending', 'running', 'completed', 'failed', 'retrying',
        name='pipeline_stage_status', create_type=False
    ), nullable=False, default='pending')
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    timeout_seconds = Column(Integer, default=30)

    job = relationship("Job", back_populates="stages")
