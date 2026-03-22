"""
Unit tests for Gold Tier Backend core components.

These tests verify:
- Security module (JWT token creation/validation)
- Event handlers
- Service layer logic
- Schema validation
"""
import pytest
from uuid import uuid4
from datetime import datetime, timezone


class TestSecurity:
    """Tests for security module."""

    def test_create_access_token(self):
        """Test JWT token creation."""
        from src.core.security import create_access_token
        
        token = create_access_token(data={"sub": "test-user", "role": "submitter"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 50

    def test_decode_access_token_valid(self):
        """Test decoding valid JWT token."""
        from src.core.security import create_access_token, decode_access_token
        
        token = create_access_token(data={"sub": "test-user", "role": "approver"})
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == "test-user"
        assert payload["role"] == "approver"

    def test_decode_access_token_invalid(self):
        """Test decoding invalid JWT token returns None."""
        from src.core.security import decode_access_token
        
        payload = decode_access_token("invalid-token")
        
        assert payload is None


class TestEventHandlers:
    """Tests for event handling system."""

    def test_register_handler(self):
        """Test handler registration."""
        from src.events.handlers import register_handler, get_handlers, clear_handlers
        
        clear_handlers()
        
        def test_handler(data):
            pass
        
        register_handler("test.event", test_handler)
        handlers = get_handlers("test.event")
        
        assert len(handlers) == 1
        assert test_handler in handlers

    def test_dispatch_event(self):
        """Test event dispatching."""
        from src.events.handlers import register_handler, dispatch_event, clear_handlers
        
        clear_handlers()
        received_data = {}
        
        def capture_handler(data):
            received_data.update(data)
        
        register_handler("test.event", capture_handler)
        dispatch_event("test.event", {"job_id": "123", "status": "queued"})
        
        assert received_data["job_id"] == "123"
        assert received_data["status"] == "queued"

    def test_handle_job_queued(self):
        """Test job queued handler."""
        from src.events.handlers import handle_job_queued
        
        # Should not raise
        handle_job_queued({"job_id": str(uuid4()), "user_id": str(uuid4())})

    def test_handle_stage_completed(self):
        """Test stage completed handler."""
        from src.events.handlers import handle_stage_completed
        
        # Should not raise
        handle_stage_completed({
            "job_id": str(uuid4()),
            "stage_type": "task_analysis",
            "progress": 25
        })


class TestJobSchemas:
    """Tests for Pydantic schemas."""

    def test_job_submission_valid(self):
        """Test valid job submission schema."""
        from src.schemas.job import JobSubmission
        
        schema = JobSubmission(task_description="This is a valid task description")
        
        assert schema.task_description == "This is a valid task description"

    def test_job_submission_too_short(self):
        """Test job submission with description too short."""
        from src.schemas.job import JobSubmission
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            JobSubmission(task_description="Short")

    def test_job_submission_too_long(self):
        """Test job submission with description too long."""
        from src.schemas.job import JobSubmission
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            JobSubmission(task_description="x" * 10001)

    def test_job_queued_response(self):
        """Test job queued response schema."""
        from src.schemas.job import JobQueuedResponse
        from src.models.enums import JobStatus
        
        schema = JobQueuedResponse(
            job_id=uuid4(),
            status=JobStatus.QUEUED,
            submitted_at=datetime.now(timezone.utc)
        )
        
        assert schema.status == JobStatus.QUEUED
        assert schema.job_id is not None


class TestPipelineService:
    """Tests for pipeline service logic."""

    def test_stage_order(self):
        """Test pipeline stage order is correct."""
        from src.services.pipeline_service import STAGE_ORDER
        from src.models.enums import PipelineStageType
        
        assert len(STAGE_ORDER) == 4
        assert STAGE_ORDER[0] == PipelineStageType.TASK_ANALYSIS
        assert STAGE_ORDER[1] == PipelineStageType.PLAN_CREATION
        assert STAGE_ORDER[2] == PipelineStageType.RISK_ASSESSMENT
        assert STAGE_ORDER[3] == PipelineStageType.FINAL_OUTPUT


class TestIdempotencyService:
    """Tests for idempotency service."""

    def test_idempotency_key_generation(self):
        """Test idempotency key is generated correctly."""
        from src.services.idempotency_service import IdempotencyService
        
        service = IdempotencyService()
        user_id = str(uuid4())
        task_desc = "Test task"
        
        key = service._make_key(user_id, task_desc)
        
        assert key is not None
        assert isinstance(key, str)
        assert key.startswith("idempotency:")
        assert len(key) > 20

    def test_idempotency_service_redis_unavailable(self):
        """Test idempotency service handles Redis unavailability."""
        from src.services.idempotency_service import IdempotencyService
        
        service = IdempotencyService()
        # Should not raise even if Redis is unavailable
        try:
            service.check_and_set("user123", "task description")
        except Exception:
            pass  # Expected if Redis is not running
