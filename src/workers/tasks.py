"""
Base Celery tasks for Gold Tier Backend.

This module defines the core task infrastructure including:
- Idempotency checks
- Error handling
- Progress tracking
- Job orchestration
"""
import logging
from uuid import UUID
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from celery import Task
from src.workers.celery_app import celery_app
from src.core.config import get_settings
from src.events.event_bus import publish_event
from src.events.types import EventType

logger = logging.getLogger("gold_tier")
settings = get_settings()


class GoldTierTask(Task):
    """
    Base task class with common functionality:
    - Idempotency checking
    - Error handling with retries
    - Progress tracking
    - Structured logging
    """
    
    abstract = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Log task failure with full context."""
        logger.error(
            f"Task {task_id} failed: {exc}",
            extra={
                "task_id": task_id,
                "task_name": self.name,
                "args": args,
                "kwargs": kwargs,
            },
            exc_info=True,
        )
    
    def on_success(self, retval, task_id, args, kwargs):
        """Log task success."""
        logger.info(f"Task {task_id} completed successfully", extra={
            "task_id": task_id,
            "task_name": self.name,
        })


def check_idempotency(key: str, ttl_seconds: int = 86400) -> bool:
    """
    Check if a task with this idempotency key was recently processed.
    
    Args:
        key: Unique idempotency key (e.g., job_id)
        ttl_seconds: How long to remember processed keys (default: 24h)
    
    Returns:
        True if task was already processed, False if it's new
    """
    try:
        from src.workers.celery_app import REDIS_URL
        import redis
        
        r = redis.from_url(REDIS_URL)
        existing = r.get(f"idempotency:{key}")
        if existing:
            logger.info(f"Duplicate task detected: {key}")
            return True
        
        # Mark as processed
        r.setex(f"idempotency:{key}", ttl_seconds, "1")
        return False
    except Exception as e:
        logger.error(f"Idempotency check failed: {e}")
        return False


def publish_progress(job_id: UUID, progress: int, stage: Optional[str] = None):
    """
    Publish progress update event.
    
    Args:
        job_id: The job UUID
        progress: Progress percentage (0-100)
        stage: Optional current stage name
    """
    try:
        publish_event(EventType.PROGRESS_UPDATE, {
            "job_id": str(job_id),
            "progress": progress,
            "stage": stage,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        logger.error(f"Failed to publish progress: {e}")


# =============================================================================
# Background Maintenance Tasks
# =============================================================================

@celery_app.task(bind=True, base=GoldTierTask)
def cleanup_old_jobs(self, retention_days: Optional[int] = None):
    """
    Delete jobs older than retention period.
    Scheduled to run daily at 2 AM.
    """
    if retention_days is None:
        retention_days = settings.RETENTION_DAYS
    
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    
    try:
        from sqlalchemy import delete
        from src.models.base import get_db_session
        from src.models.job import Job
        
        db = next(get_db_session())
        try:
            # Delete old jobs (cascade will handle related records)
            result = db.execute(
                delete(Job).where(Job.submitted_at < cutoff)
            )
            db.commit()
            deleted_count = result.rowcount
            logger.info(f"Cleaned up {deleted_count} jobs older than {retention_days} days")
            return {"deleted_count": deleted_count}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise


@celery_app.task(bind=True, base=GoldTierTask)
def check_approval_timeout(self):
    """
    Check for approvals that have timed out.
    Scheduled to run every 30 minutes.
    """
    timeout_hours = 24  # Default approval SLA
    
    try:
        from sqlalchemy import select
        from datetime import timedelta
        from src.models.base import get_db_session
        from src.models.plan import Plan
        from src.models.enums import ApprovalStatus
        
        db = next(get_db_session())
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=timeout_hours)
            
            # Find pending approvals past timeout
            stmt = select(Plan).where(
                Plan.approval_status == ApprovalStatus.PENDING,
                Plan.created_at < cutoff,
            )
            plans = db.execute(stmt).scalars().all()
            
            for plan in plans:
                logger.warning(f"Approval timeout for plan {plan.id}")
                plan.approval_status = ApprovalStatus.TIMEOUT
                db.commit()
                
                publish_event(EventType.APPROVAL_TIMEOUT, {
                    "plan_id": str(plan.id),
                    "job_id": str(plan.job_id),
                    "timeout_hours": timeout_hours,
                })
            
            logger.info(f"Checked approval timeouts: {len(plans)} timed out")
            return {"timed_out_count": len(plans)}
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Approval timeout check failed: {e}")
        raise


# =============================================================================
# Job Processing Task
# =============================================================================

@celery_app.task(bind=True, base=GoldTierTask)
def process_job(self, job_id: str):
    """
    Main job processing task.
    Starts the pipeline and orchestrates stage execution.
    
    Args:
        job_id: The job UUID as string
    """
    # Idempotency check
    if check_idempotency(job_id):
        logger.info(f"Skipping duplicate job: {job_id}")
        return {"status": "skipped", "reason": "duplicate"}
    
    try:
        from uuid import UUID
        from sqlalchemy.orm import Session
        from src.models.base import get_db_session
        from src.services.pipeline_service import PipelineService
        
        job_uuid = UUID(job_id)
        
        # Start pipeline
        db: Session = next(get_db_session())
        try:
            pipeline_service = PipelineService(db)
            pipeline_service.start_pipeline(job_uuid)
            logger.info(f"Started pipeline for job {job_id}")
        finally:
            db.close()
        
        # Trigger first stage (task analysis)
        from src.workers.stages.task_analysis import process as task_analysis
        task_analysis.delay(job_id)
        
        return {"status": "started", "job_id": job_id}
    
    except Exception as e:
        logger.error(f"Failed to start job processing: {e}", exc_info=True)
        publish_event(EventType.JOB_FAILED, {
            "job_id": job_id,
            "error": str(e),
        })
        raise
