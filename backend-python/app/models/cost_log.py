import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, DateTime, Numeric, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class CostLog(Base):
    __tablename__ = "CostLog"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    agentExecutionId: Mapped[str | None] = mapped_column(String, ForeignKey("AgentExecution.id", ondelete="SET NULL"), nullable=True)
    modelName: Mapped[str] = mapped_column(String, nullable=False)
    tokensIn: Mapped[int] = mapped_column(Integer, nullable=False)
    tokensOut: Mapped[int] = mapped_column(Integer, nullable=False)
    estimatedCostUsd: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    execution = relationship("AgentExecution", back_populates="costLogs")

    __table_args__ = (Index("ix_costlog_createdAt", "createdAt"),)
