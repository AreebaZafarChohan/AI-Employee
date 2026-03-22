import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, Index
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Goal(Base):
    __tablename__ = "Goal"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    state: Mapped[str] = mapped_column(String, default="PENDING_PLAN")
    priority: Mapped[int] = mapped_column(Integer, default=1)
    userId: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updatedAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_goal_state", "state"),
        Index("ix_goal_createdAt", "createdAt"),
    )
