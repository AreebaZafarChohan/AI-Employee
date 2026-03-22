import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Index, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Task(Base):
    __tablename__ = "Task"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    goalId: Mapped[str | None] = mapped_column(String, ForeignKey("Goal.id", ondelete="CASCADE"), nullable=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    order: Mapped[int] = mapped_column(Integer, default=0)
    assignedAgent: Mapped[str | None] = mapped_column(String, nullable=True)
    dependsOn: Mapped[list[str] | None] = mapped_column(ARRAY(String), default=[])
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completedAt: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    goal = relationship("Goal", back_populates="tasks")
    executions = relationship("AgentExecution", back_populates="task", cascade="all, delete-orphan")
    plan = relationship("Plan", back_populates="task", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_task_status", "status"),
        Index("ix_task_createdAt", "createdAt"),
    )
