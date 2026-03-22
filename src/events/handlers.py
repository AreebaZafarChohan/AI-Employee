import logging
from typing import Callable
from src.events.types import EventType

logger = logging.getLogger("gold_tier")

_handlers: dict[str, list[Callable]] = {}


def register_handler(event_type: str, handler: Callable):
    """Register an event handler for a specific event type."""
    _handlers.setdefault(event_type, []).append(handler)


def dispatch_event(event_type: str, data: dict):
    """Dispatch an event to all registered handlers."""
    handlers = _handlers.get(event_type, [])
    for handler in handlers:
        try:
            handler(data)
        except Exception as e:
            logger.error(f"Handler error for {event_type}: {e}", exc_info=True)


def get_handlers(event_type: str) -> list[Callable]:
    """Get all handlers for an event type."""
    return _handlers.get(event_type, [])


def clear_handlers():
    """Clear all registered handlers (useful for testing)."""
    _handlers.clear()


# =============================================================================
# Job Lifecycle Handlers
# =============================================================================

def handle_job_queued(data: dict):
    """Handle job queued event - log and notify."""
    job_id = data.get("job_id")
    logger.info(f"Job queued: {job_id}", extra={
        "event": EventType.JOB_QUEUED,
        "job_id": job_id,
        "user_id": data.get("user_id"),
    })


def handle_job_completed(data: dict):
    """Handle job completed event - log and trigger notifications."""
    job_id = data.get("job_id")
    logger.info(f"Job completed: {job_id}", extra={
        "event": EventType.JOB_COMPLETED,
        "job_id": job_id,
        "duration_ms": data.get("duration_ms"),
    })


def handle_job_failed(data: dict):
    """Handle job failed event - log error and notify."""
    job_id = data.get("job_id")
    error = data.get("error", "Unknown error")
    logger.error(f"Job failed: {job_id} - {error}", extra={
        "event": EventType.JOB_FAILED,
        "job_id": job_id,
        "error": error,
    })


# =============================================================================
# Pipeline Stage Handlers
# =============================================================================

def handle_stage_started(data: dict):
    """Handle stage started event - update status and notify."""
    job_id = data.get("job_id")
    stage_type = data.get("stage_type")
    logger.info(f"Stage started: {stage_type} for job {job_id}", extra={
        "event": EventType.STAGE_STARTED,
        "job_id": job_id,
        "stage_type": stage_type,
    })


def handle_stage_completed(data: dict):
    """Handle stage completed event - store output and trigger next stage."""
    job_id = data.get("job_id")
    stage_type = data.get("stage_type")
    progress = data.get("progress", 0)
    logger.info(f"Stage completed: {stage_type} for job {job_id} (progress: {progress}%)", extra={
        "event": EventType.STAGE_COMPLETED,
        "job_id": job_id,
        "stage_type": stage_type,
        "progress": progress,
    })


def handle_stage_failed(data: dict):
    """Handle stage failed event - retry or mark as failed."""
    job_id = data.get("job_id")
    stage_type = data.get("stage_type")
    retry_count = data.get("retry_count", 0)
    error = data.get("error", "Unknown error")
    logger.warning(f"Stage failed: {stage_type} for job {job_id}, retry: {retry_count}/3 - {error}", extra={
        "event": EventType.STAGE_FAILED,
        "job_id": job_id,
        "stage_type": stage_type,
        "retry_count": retry_count,
        "error": error,
    })


# =============================================================================
# Approval Workflow Handlers
# =============================================================================

def handle_plan_pending_approval(data: dict):
    """Handle plan pending approval - notify approvers."""
    plan_id = data.get("plan_id")
    job_id = data.get("job_id")
    logger.info(f"Plan pending approval: {plan_id} for job {job_id}", extra={
        "event": EventType.PLAN_PENDING_APPROVAL,
        "plan_id": plan_id,
        "job_id": job_id,
    })


def handle_plan_approved(data: dict):
    """Handle plan approved - log decision and enable execution."""
    plan_id = data.get("plan_id")
    approver_id = data.get("approver_id")
    logger.info(f"Plan approved: {plan_id} by {approver_id}", extra={
        "event": EventType.PLAN_APPROVED,
        "plan_id": plan_id,
        "approver_id": approver_id,
    })


def handle_plan_rejected(data: dict):
    """Handle plan rejected - log and trigger regeneration."""
    plan_id = data.get("plan_id")
    approver_id = data.get("approver_id")
    comments = data.get("comments", "No comments provided")
    logger.info(f"Plan rejected: {plan_id} by {approver_id} - {comments}", extra={
        "event": EventType.PLAN_REJECTED,
        "plan_id": plan_id,
        "approver_id": approver_id,
        "comments": comments,
    })


def handle_approval_timeout(data: dict):
    """Handle approval timeout - escalate or auto-reject."""
    plan_id = data.get("plan_id")
    job_id = data.get("job_id")
    timeout_hours = data.get("timeout_hours", 24)
    logger.warning(f"Approval timeout: {plan_id} for job {job_id} after {timeout_hours}h", extra={
        "event": EventType.APPROVAL_TIMEOUT,
        "plan_id": plan_id,
        "job_id": job_id,
        "timeout_hours": timeout_hours,
    })


# =============================================================================
# Progress Update Handler
# =============================================================================

def handle_progress_update(data: dict):
    """Handle progress update - forward to WebSocket clients."""
    job_id = data.get("job_id")
    progress = data.get("progress", 0)
    logger.debug(f"Progress update: job {job_id} at {progress}%", extra={
        "event": EventType.PROGRESS_UPDATE,
        "job_id": job_id,
        "progress": progress,
    })


# =============================================================================
# Register Default Handlers
# =============================================================================

register_handler(EventType.JOB_QUEUED, handle_job_queued)
register_handler(EventType.JOB_COMPLETED, handle_job_completed)
register_handler(EventType.JOB_FAILED, handle_job_failed)
register_handler(EventType.STAGE_STARTED, handle_stage_started)
register_handler(EventType.STAGE_COMPLETED, handle_stage_completed)
register_handler(EventType.STAGE_FAILED, handle_stage_failed)
register_handler(EventType.PLAN_PENDING_APPROVAL, handle_plan_pending_approval)
register_handler(EventType.PLAN_APPROVED, handle_plan_approved)
register_handler(EventType.PLAN_REJECTED, handle_plan_rejected)
register_handler(EventType.APPROVAL_TIMEOUT, handle_approval_timeout)
register_handler(EventType.PROGRESS_UPDATE, handle_progress_update)
