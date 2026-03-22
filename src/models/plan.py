from sqlalchemy import Column, Integer, Enum, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from src.models.base import Base, UUIDMixin, TimestampMixin
from src.models.enums import ApprovalStatus


class Plan(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "plans"
    
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), unique=True, nullable=False)
    version = Column(Integer, default=1)
    task_analysis = Column(JSONB, nullable=True)
    recommended_actions = Column(JSONB, nullable=True)
    risk_assessment = Column(JSONB, nullable=True)
    approval_status = Column(Enum(ApprovalStatus), nullable=False, default=ApprovalStatus.DRAFT)
    
    job = relationship("Job", back_populates="plan")
    approval_events = relationship("ApprovalEvent", back_populates="plan", order_by="ApprovalEvent.decided_at")
