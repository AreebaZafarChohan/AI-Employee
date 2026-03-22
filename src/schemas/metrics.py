from pydantic import BaseModel


class QueueMetrics(BaseModel):
    queued_count: int
    processing_count: int
    completed_today: int
    failed_today: int
    avg_completion_time_seconds: float | None = None
    pending_approval_count: int
