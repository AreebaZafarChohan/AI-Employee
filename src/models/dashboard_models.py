"""SQLAlchemy models mirroring the Prisma schema for the dashboard."""

import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from src.models.sqlite_db import Base


def _utcnow():
    return datetime.now(timezone.utc)


def _uuid():
    return str(uuid.uuid4())


class Task(Base):
    __tablename__ = "Task"

    id = Column(String, primary_key=True, default=_uuid)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String, default="Pending", index=True)
    createdAt = Column(DateTime, default=_utcnow, index=True)
    updatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    completedAt = Column(DateTime, nullable=True)

    plan = relationship("Plan", back_populates="task", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
            "completedAt": self.completedAt.isoformat() if self.completedAt else None,
        }


class Plan(Base):
    __tablename__ = "Plan"

    id = Column(String, primary_key=True, default=_uuid)
    taskId = Column(String, ForeignKey("Task.id", ondelete="CASCADE"), unique=True, nullable=False)
    status = Column(String, default="Draft", index=True)
    createdAt = Column(DateTime, default=_utcnow)
    updatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    task = relationship("Task", back_populates="plan")
    steps = relationship("PlanStep", back_populates="plan", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "taskId": self.taskId,
            "status": self.status,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
            "steps": [s.to_dict() for s in self.steps] if self.steps else [],
        }


class PlanStep(Base):
    __tablename__ = "PlanStep"

    id = Column(String, primary_key=True, default=_uuid)
    planId = Column(String, ForeignKey("Plan.id", ondelete="CASCADE"), index=True, nullable=False)
    order = Column(Integer, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    estimatedDuration = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False)
    createdAt = Column(DateTime, default=_utcnow)

    plan = relationship("Plan", back_populates="steps")

    def to_dict(self):
        return {
            "id": self.id,
            "planId": self.planId,
            "order": self.order,
            "title": self.title,
            "description": self.description,
            "estimatedDuration": self.estimatedDuration,
            "completed": self.completed,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None,
        }


class ActivityLog(Base):
    __tablename__ = "ActivityLog"

    id = Column(String, primary_key=True, default=_uuid)
    type = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=_utcnow, index=True)
    extra_metadata = Column("metadata", Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "metadata": self.extra_metadata,
        }


class SystemState(Base):
    __tablename__ = "system_state"

    id = Column(String, primary_key=True)
    state = Column(String, nullable=False)
    lastActivity = Column(DateTime, nullable=False)
    updatedAt = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "state": self.state,
            "lastActivity": self.lastActivity.isoformat() if self.lastActivity else None,
            "updatedAt": self.updatedAt.isoformat() if self.updatedAt else None,
        }
