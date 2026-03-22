"""
Pytest configuration and fixtures for Gold Tier Backend tests.

Usage:
    pytest tests/                          # Run all tests
    pytest tests/contract/                 # Run contract tests
    pytest tests/integration/              # Run integration tests
    pytest tests/unit/                     # Run unit tests
    pytest -v --cov=src                    # Run with coverage
"""
import os
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, Column, String, Integer, DateTime
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool
from datetime import datetime, timezone
import uuid

from src.api.main import app
from src.models.base import get_db
from src.models.user import User
from src.models.enums import UserRole, JobStatus


# Simple in-memory base for tests that don't need full schema
class TestBase(DeclarativeBase):
    pass


# Minimal test models (avoid JSONB for SQLite compatibility)
class TestUser(TestBase):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, nullable=False)
    role = Column(String, default="submitter")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TestJob(TestBase):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_description = Column(String, nullable=False)
    status = Column(String, default="queued")
    progress_percentage = Column(Integer, default=0)
    submitted_by = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine (in-memory SQLite)."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestBase.metadata.create_all(bind=engine)
    yield engine
    TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionTesting()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """Create test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db_session: Session) -> dict:
    """Create a test user (submitter role) - returns dict for simplicity."""
    from src.core.security import create_access_token
    
    user_data = {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "role": "submitter"
    }
    
    # Create token for this user
    token = create_access_token(data={"sub": user_data["id"], "role": user_data["role"]})
    user_data["token"] = token
    
    return user_data


@pytest.fixture
def test_approver(db_session: Session) -> dict:
    """Create a test user (approver role) - returns dict for simplicity."""
    from src.core.security import create_access_token
    
    user_data = {
        "id": str(uuid.uuid4()),
        "email": "approver@example.com",
        "role": "approver"
    }
    
    # Create token for this user
    token = create_access_token(data={"sub": user_data["id"], "role": user_data["role"]})
    user_data["token"] = token
    
    return user_data


@pytest.fixture
def auth_headers(test_user: dict) -> dict:
    """Get authentication headers for test user."""
    return {"Authorization": f"Bearer {test_user['token']}"}


@pytest.fixture
def approver_headers(test_approver: dict) -> dict:
    """Get authentication headers for test approver."""
    return {"Authorization": f"Bearer {test_approver['token']}"}
