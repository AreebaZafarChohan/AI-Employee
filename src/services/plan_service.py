from uuid import UUID
from sqlalchemy.orm import Session
from src.models.plan import Plan
from src.models.enums import ApprovalStatus
from src.core.exceptions import PlanNotFoundError
from src.events.event_bus import publish_event
from src.events.types import EventType


class PlanService:
    def __init__(self, db: Session):
        self.db = db

    def create_plan_from_pipeline(self, job_id: UUID, task_analysis: dict, recommended_actions: dict, risk_assessment: dict) -> Plan:
        plan = Plan(
            job_id=job_id,
            task_analysis=task_analysis,
            recommended_actions=recommended_actions,
            risk_assessment=risk_assessment,
            approval_status=ApprovalStatus.PENDING_APPROVAL,
        )
        self.db.add(plan)
        self.db.commit()
        self.db.refresh(plan)
        publish_event(EventType.PLAN_PENDING_APPROVAL, {"plan_id": str(plan.id), "job_id": str(job_id)})
        return plan

    def get_plan(self, plan_id: UUID) -> Plan:
        plan = self.db.query(Plan).filter(Plan.id == plan_id).first()
        if not plan:
            raise PlanNotFoundError(str(plan_id))
        return plan

    def update_approval_status(self, plan_id: UUID, status: ApprovalStatus):
        plan = self.get_plan(plan_id)
        plan.approval_status = status
        self.db.commit()
        return plan
