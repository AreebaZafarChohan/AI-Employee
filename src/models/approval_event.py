from sqlalchemy import Column, Text, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from src.models.base import Base, UUIDMixin
from src.models.enums import ApprovalDecision


class ApprovalEvent(Base, UUIDMixin):
    __tablename__ = "approval_events"
    
    plan_id = Column(UUID(as_uuid=True), ForeignKey("plans.id"), nullable=False, index=True)
    decision = Column(Enum(ApprovalDecision), nullable=False)
    approver_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    decided_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    comments = Column(Text, nullable=True)
    
    plan = relationship("Plan", back_populates="approval_events")
    approver = relationship("User")
