import uuid
from datetime import datetime
from sqlalchemy import String, Float, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ToolInvocation(Base):
    __tablename__ = "ToolInvocation"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agentExecutionId: Mapped[str] = mapped_column(String, ForeignKey("AgentExecution.id", ondelete="CASCADE"), nullable=False)
    toolName: Mapped[str] = mapped_column(String, nullable=False)
    arguments: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    riskScore: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING_APPROVAL")
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    execution = relationship("AgentExecution", back_populates="toolInvocations")

    __table_args__ = (
        Index("ix_toolinvocation_toolName", "toolName"),
        Index("ix_toolinvocation_status", "status"),
    )
