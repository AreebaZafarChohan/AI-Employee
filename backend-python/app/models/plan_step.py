import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PlanStep(Base):
    __tablename__ = "PlanStep"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    planId: Mapped[str] = mapped_column(String, ForeignKey("Plan.id", ondelete="CASCADE"), nullable=False)
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    estimatedDuration: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan = relationship("Plan", back_populates="steps")

    __table_args__ = (
        Index("ix_planstep_planId", "planId"),
        Index("ix_planstep_order", "order"),
    )
