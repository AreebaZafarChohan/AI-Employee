import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Plan(Base):
    __tablename__ = "Plan"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    taskId: Mapped[str] = mapped_column(String, ForeignKey("Task.id", ondelete="CASCADE"), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String, default="Draft")
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="plan")
    steps = relationship("PlanStep", back_populates="plan", cascade="all, delete-orphan", order_by="PlanStep.order")

    __table_args__ = (Index("ix_plan_status", "status"),)
