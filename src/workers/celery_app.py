"""
Celery application configuration for Gold Tier Backend.

Usage:
    celery -A src.workers.celery_app worker --loglevel=info
    celery -A src.workers.celery_app beat --loglevel=info
"""
import os
from celery import Celery
from celery.schedules import crontab

# Load configuration from environment
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Create Celery app
celery_app = Celery(
    "gold_tier",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["src.workers.tasks"],
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task routes (route tasks to specific queues)
    task_routes={
        "src.workers.stages.task_analysis.process": {"queue": "default"},
        "src.workers.stages.plan_creation.process": {"queue": "default"},
        "src.workers.stages.risk_assessment.process": {"queue": "risk"},
        "src.workers.stages.final_output.process": {"queue": "default"},
        "src.services.notification_service.send_email": {"queue": "io"},
    },
    
    # Worker pools
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    
    # Retry configuration
    task_annotations={
        "*": {
            "max_retries": 3,
            "autoretry_for": (ConnectionError, TimeoutError, OSError),
        }
    },
    
    # Rate limiting
    task_default_rate_limit="100/m",
    
    # Results expiration (1 hour)
    result_expires=3600,
    
    # Broker connection settings
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=5,
    
    # Task time limits (30 seconds per stage)
    task_time_limit=30,
    task_soft_time_limit=25,
    
    # Scheduled tasks (Celery Beat)
    beat_schedule={
        "cleanup-old-jobs": {
            "task": "src.workers.tasks.cleanup_old_jobs",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
        "check-approval-timeouts": {
            "task": "src.workers.tasks.check_approval_timeout",
            "schedule": crontab(minute="*/30"),  # Every 30 minutes
        },
    },
)

# Auto-discover tasks in submodules
celery_app.autodiscover_tasks(["src.workers.stages"])


@celery_app.task(bind=True)
def debug_task(self):
    """Debug task to verify Celery is working."""
    print(f"Request: {self.request!r}")
    return "Celery is working!"


if __name__ == "__main__":
    # For local testing
    celery_app.start()
