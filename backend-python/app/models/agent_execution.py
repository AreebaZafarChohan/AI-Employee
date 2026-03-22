import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AgentExecution(Base):
    __tablename__ = "AgentExecution"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    taskId: Mapped[str] = mapped_column(String, ForeignKey("Task.id", ondelete="CASCADE"), nullable=False)
    agentName: Mapped[str] = mapped_column(String, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(String, nullable=True)
    toolCalls: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="SUCCESS")
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="executions")
    costLogs = relationship("CostLog", back_populates="execution")
    toolInvocations = relationship("ToolInvocation", back_populates="execution", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_agentexecution_taskId", "taskId"),
        Index("ix_agentexecution_agentName", "agentName"),
    )
