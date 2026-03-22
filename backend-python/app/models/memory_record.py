import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class MemoryRecord(Base):
    __tablename__ = "MemoryRecord"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    content: Mapped[str] = mapped_column(String, nullable=False)
    goalId: Mapped[str | None] = mapped_column(String, nullable=True)
    taskId: Mapped[str | None] = mapped_column(String, nullable=True)
    userId: Mapped[str | None] = mapped_column(String, nullable=True)
    createdAt: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (Index("ix_memoryrecord_createdAt", "createdAt"),)
