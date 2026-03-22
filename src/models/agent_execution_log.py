from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
from src.models.base import Base, UUIDMixin
from src.models.enums import AgentType, AgentExecutionStatus


class AgentExecutionLog(Base, UUIDMixin):
    __tablename__ = "agent_execution_logs"
    
    agent_type = Column(Enum(AgentType), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False, index=True)
    stage_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_stages.id"), nullable=True)
    input_data = Column(JSONB, nullable=True)
    output_data = Column(JSONB, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    status = Column(Enum(AgentExecutionStatus), nullable=False, default=AgentExecutionStatus.RUNNING)
    executed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
