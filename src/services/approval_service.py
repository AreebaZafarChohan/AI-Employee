from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from src.models.approval_event import ApprovalEvent
from src.models.enums import ApprovalDecision, ApprovalStatus, JobStatus
from src.services.plan_service import PlanService
from src.services.job_service import JobService
from src.events.event_bus import publish_event
from src.events.types import EventType


class ApprovalService:
    def __init__(self, db: Session):
        self.db = db
        self.plan_service = PlanService(db)
        self.job_service = JobService(db)

    def approve_plan(self, plan_id: UUID, approver_id: UUID, comments: str | None = None) -> ApprovalEvent:
        plan = self.plan_service.get_plan(plan_id)
        plan.approval_status = ApprovalStatus.APPROVED
        event = ApprovalEvent(
            plan_id=plan_id, decision=ApprovalDecision.APPROVED,
            approver_id=approver_id, comments=comments,
        )
        self.db.add(event)
        self.db.commit()
        publish_event(EventType.PLAN_APPROVED, {"plan_id": str(plan_id), "approver_id": str(approver_id)})
        return event

    def reject_plan(self, plan_id: UUID, approver_id: UUID, comments: str, db: Session | None = None) -> tuple[ApprovalEvent, UUID | None]:
        plan = self.plan_service.get_plan(plan_id)
        plan.approval_status = ApprovalStatus.REJECTED
        event = ApprovalEvent(
            plan_id=plan_id, decision=ApprovalDecision.REJECTED,
            approver_id=approver_id, comments=comments,
        )
        self.db.add(event)
        # Create regeneration job
        job = self.job_service.get_job(plan.job_id)
        new_job = self.job_service.create_job(
            task_description=f"[Regeneration] {job.task_description}\n\nFeedback: {comments}",
            submitted_by=job.submitted_by,
        )
        new_job.parent_job_id = job.id
        self.db.commit()
        publish_event(EventType.PLAN_REJECTED, {
            "plan_id": str(plan_id), "approver_id": str(approver_id),
            "regeneration_job_id": str(new_job.id),
        })
        return event, new_job.id
