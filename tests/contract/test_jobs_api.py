"""
Contract tests for Jobs API endpoints.

Tests verify:
- Valid request returns expected response
- Invalid request returns 422
- Authentication is required (401 without token)
- Authorization works correctly (403 for unauthorized access)
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


class TestJobSubmission:
    """Tests for POST /api/v1/jobs endpoint."""

    def test_submit_job_valid_request(self, client: TestClient, auth_headers: dict):
        """Valid job submission returns 201 with job_id."""
        payload = {
            "task_description": "Create a sales email template for new product launch"
        }
        
        response = client.post("/api/v1/jobs", json=payload, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "submitted_at" in data

    def test_submit_job_invalid_request_empty_description(self, client: TestClient, auth_headers: dict):
        """Empty task description returns 422."""
        payload = {"task_description": ""}
        
        response = client.post("/api/v1/jobs", json=payload, headers=auth_headers)
        
        assert response.status_code == 422

    def test_submit_job_invalid_request_too_short(self, client: TestClient, auth_headers: dict):
        """Task description under 10 chars returns 422."""
        payload = {"task_description": "Too short"}
        
        response = client.post("/api/v1/jobs", json=payload, headers=auth_headers)
        
        assert response.status_code == 422

    def test_submit_job_no_auth_returns_401(self, client: TestClient):
        """Request without authentication returns 401."""
        payload = {
            "task_description": "Create a sales email template for new product launch"
        }
        
        response = client.post("/api/v1/jobs", json=payload)
        
        assert response.status_code == 401


class TestGetJob:
    """Tests for GET /api/v1/jobs/{job_id} endpoint."""

    def test_get_job_exists(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Get existing job returns 200 with job details."""
        from tests.conftest import create_test_job
        from src.core.security import create_access_token
        from src.models.user import User
        
        # Get user from database
        user = db_session.query(User).first()
        job = create_test_job(db_session, user.id, "Test task description")
        
        response = client.get(f"/api/v1/jobs/{job.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job.id)
        assert data["task_description"] == "Test task description"
        assert data["status"] == "queued"

    def test_get_job_not_found_returns_404(self, client: TestClient, auth_headers: dict):
        """Get non-existent job returns 404."""
        import uuid
        fake_id = uuid.uuid4()
        
        response = client.get(f"/api/v1/jobs/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404

    def test_get_job_unauthorized_returns_403(self, client: TestClient, auth_headers: dict, db_session: Session, test_approver: User):
        """Get another user's job (as submitter) returns 403."""
        from tests.conftest import create_test_job
        
        # Create job for different user
        job = create_test_job(db_session, test_approver.id, "Another user's task")
        
        response = client.get(f"/api/v1/jobs/{job.id}", headers=auth_headers)
        
        assert response.status_code == 403


class TestListJobs:
    """Tests for GET /api/v1/jobs endpoint."""

    def test_list_jobs_returns_paginated_response(self, client: TestClient, auth_headers: dict):
        """List jobs returns paginated response."""
        response = client.get("/api/v1/jobs", headers=auth_headers, params={"page": 1, "page_size": 20})
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 20

    def test_list_jobs_filter_by_status(self, client: TestClient, auth_headers: dict):
        """List jobs with status filter."""
        response = client.get("/api/v1/jobs", headers=auth_headers, params={"status": "queued", "page": 1})
        
        assert response.status_code == 200


class TestJobHistory:
    """Tests for GET /api/v1/jobs/{job_id}/history endpoint."""

    def test_get_job_history(self, client: TestClient, auth_headers: dict, db_session: Session):
        """Get job history returns complete audit trail."""
        from tests.conftest import create_test_job
        from src.core.security import create_access_token
        from src.models.user import User
        
        user = db_session.query(User).first()
        job = create_test_job(db_session, user.id, "Test task with history")
        
        response = client.get(f"/api/v1/jobs/{job.id}/history", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job.id)
        assert "stages" in data
        assert "agent_logs" in data
        assert "approval_events" in data
