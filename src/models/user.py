from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import ENUM as PostgreSQLEnum
from datetime import datetime, timezone
from src.models.base import Base, UUIDMixin, TimestampMixin
from src.models.enums import UserRole


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Optional for now
    role = Column(PostgreSQLEnum('submitter', 'approver', name='user_role', create_type=False), nullable=False, default='submitter')
    last_login_at = Column(DateTime(timezone=True), nullable=True)
