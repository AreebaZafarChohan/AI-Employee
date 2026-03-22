"""SQLite database engine, session factory, and FastAPI dependency."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from src.core.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.SQLITE_URL,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session_factory():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), autocommit=False, autoflush=False)
    return _SessionLocal


def get_db():
    """FastAPI dependency that yields a SQLAlchemy session."""
    db = get_session_factory()()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables defined in dashboard_models."""
    from src.models.dashboard_models import Task, Plan, PlanStep, ActivityLog, SystemState  # noqa: F401
    Base.metadata.create_all(bind=get_engine())
