from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.models.job import Job
from src.models.enums import JobStatus
from src.core.exceptions import JobNotFoundError


class JobService:
    def __init__(self, db: Session):
        self.db = db

    def create_job(self, task_description: str, submitted_by: UUID) -> Job:
        job = Job(
            task_description=task_description,
            status=JobStatus.QUEUED,
            submitted_by=submitted_by,
            submitted_at=datetime.now(timezone.utc),
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get_job(self, job_id: UUID) -> Job:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise JobNotFoundError(str(job_id))
        return job

    def list_jobs(self, user_id: UUID, status: JobStatus | None = None, page: int = 1, page_size: int = 20):
        query = self.db.query(Job).filter(Job.submitted_by == user_id)
        if status:
            query = query.filter(Job.status == status)
        total = query.count()
        items = query.order_by(Job.submitted_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return items, total

    def update_status(self, job_id: UUID, status: JobStatus, progress: int | None = None):
        job = self.get_job(job_id)
        job.status = status
        if progress is not None:
            job.progress_percentage = progress
        if status == JobStatus.COMPLETED:
            job.completed_at = datetime.now(timezone.utc)
        self.db.commit()
        return job

    def validate_task_description(self, desc: str) -> bool:
        return 10 <= len(desc) <= 10000
