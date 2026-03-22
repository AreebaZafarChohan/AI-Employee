import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class ActivityLog(Base):
    __tablename__ = "ActivityLog"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    type: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    extra_metadata: Mapped[str | None] = mapped_column("metadata", String, nullable=True)

    __table_args__ = (
        Index("ix_activitylog_timestamp", "timestamp"),
        Index("ix_activitylog_type", "type"),
    )
