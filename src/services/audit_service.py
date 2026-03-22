from uuid import UUID
from sqlalchemy.orm import Session
from src.models.job import Job
from src.models.pipeline_stage import PipelineStage
from src.models.agent_execution_log import AgentExecutionLog
from src.models.approval_event import ApprovalEvent
from src.models.plan import Plan
from src.core.exceptions import JobNotFoundError


class AuditService:
    def __init__(self, db: Session):
        self.db = db

    def get_job_history(self, job_id: UUID) -> dict:
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise JobNotFoundError(str(job_id))
        stages = self.db.query(PipelineStage).filter(PipelineStage.job_id == job_id).order_by(PipelineStage.started_at).all()
        agent_logs = self.db.query(AgentExecutionLog).filter(AgentExecutionLog.job_id == job_id).order_by(AgentExecutionLog.executed_at).all()
        plan = self.db.query(Plan).filter(Plan.job_id == job_id).first()
        approval_events = []
        if plan:
            approval_events = self.db.query(ApprovalEvent).filter(ApprovalEvent.plan_id == plan.id).order_by(ApprovalEvent.decided_at).all()
        return {"job": job, "stages": stages, "agent_logs": agent_logs, "approval_events": approval_events}
