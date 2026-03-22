"""
Risk Assessment Stage Worker

This is the third stage of the 4-stage pipeline.
It evaluates potential risks, assigns severity scores, and suggests mitigations.

Input: Plan output from stage 2
Output: Risk assessment with severity scores and mitigation strategies
"""
import logging
from uuid import UUID
from datetime import datetime, timezone
from src.workers.celery_app import celery_app
from src.workers.tasks import GoldTierTask, check_idempotency, publish_progress
from src.events.event_bus import publish_event
from src.events.types import EventType

logger = logging.getLogger("gold_tier")


@celery_app.task(bind=True, base=GoldTierTask, max_retries=3)
def process(self, job_id: str):
    """
    Risk Assessment Stage: Evaluate risks and suggest mitigations.
    
    Args:
        job_id: The job UUID as string
    """
    stage_id = None
    
    try:
        from sqlalchemy.orm import Session
        from src.models.base import get_db_session
        from src.models.pipeline_stage import PipelineStage
        from src.models.enums import PipelineStageStatus
        from src.models.plan import Plan
        
        job_uuid = UUID(job_id)
        db: Session = next(get_db_session())
        
        try:
            # Get the plan output from previous stage
            plan = db.query(Plan).filter(
                Plan.job_id == job_uuid,
            ).first()
            
            if not plan:
                raise ValueError(f"Plan not found for job {job_id}")
            
            plan_data = {
                "objectives": plan.task_analysis or {},
                "recommended_actions": plan.recommended_actions or [],
            }
            
            # Create pipeline stage record
            stage = PipelineStage(
                job_id=job_uuid,
                stage_type="risk_assessment",
                status=PipelineStageStatus.RUNNING,
                input_data={"plan": plan_data},
                started_at=datetime.now(timezone.utc),
                timeout_seconds=30,
            )
            db.add(stage)
            db.commit()
            stage_id = stage.id
            
            logger.info(f"Risk assessment started for job {job_id}")
            publish_event(EventType.STAGE_STARTED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "risk_assessment",
            })
            
            # Perform risk assessment
            risk_result = _assess_risks(plan_data)
            
            # Update progress
            publish_progress(job_uuid, 75, "risk_assessment")
            
            # Update plan with risk assessment
            plan.risk_assessment = risk_result
            db.commit()
            
            # Store output
            stage.output_data = risk_result
            stage.status = PipelineStageStatus.COMPLETED
            stage.completed_at=datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Risk assessment completed for job {job_id}")
            publish_event(EventType.STAGE_COMPLETED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "risk_assessment",
                "progress": 75,
                "output": risk_result,
            })
            
            # Trigger next stage: Final Output
            from src.workers.stages.final_output import process as final_output
            final_output.delay(job_id)
            
            return {"status": "completed", "stage_id": str(stage_id), "risks": risk_result}
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Risk assessment failed for job {job_id}: {e}", exc_info=True)
        
        if stage_id:
            try:
                db: Session = next(get_db_session())
                stage = db.query(PipelineStage).filter(PipelineStage.id == stage_id).first()
                if stage:
                    stage.status = PipelineStageStatus.FAILED
                    stage.error_message = str(e)
                    db.commit()
                db.close()
            except Exception:
                pass
        
        publish_event(EventType.STAGE_FAILED, {
            "job_id": job_id,
            "stage_type": "risk_assessment",
            "error": str(e),
            "retry_count": self.request.retries,
        })
        
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


def _assess_risks(plan_data: dict) -> dict:
    """
    Assess risks for the proposed plan.
    
    In production, this would use AI/LLM to identify risks.
    For now, we use rule-based risk identification.
    
    Returns:
        dict with:
            - overall_risk_level: low/medium/high
            - risks: List of identified risks with severity
            - mitigations: Suggested mitigation strategies
            - approval_required: Boolean indicating if human approval is needed
    """
    actions = plan_data.get("recommended_actions", [])
    objectives = plan_data.get("objectives", {})
    complexity = objectives.get("complexity", "medium") if isinstance(objectives, dict) else "medium"
    
    # Risk identification rules
    risks = []
    
    # Complexity-based risks
    if complexity == "high":
        risks.append({
            "id": "R1",
            "category": "complexity",
            "description": "High complexity increases chance of unforeseen issues",
            "severity": "medium",
            "probability": 0.6,
            "impact": "Schedule delays, quality issues",
        })
    
    # Timeline risks
    timeline = plan_data.get("timeline", "")
    if "week" in timeline.lower() or "days" in timeline.lower():
        num_days = int(''.join(filter(str.isdigit, timeline)) or "5")
        if num_days > 5:
            risks.append({
                "id": "R2",
                "category": "timeline",
                "description": "Extended timeline increases risk of scope creep",
                "severity": "low",
                "probability": 0.4,
                "impact": "Delayed delivery, stakeholder frustration",
            })
    
    # Resource risks
    resources = plan_data.get("resources", [])
    if len(resources) <= 2:
        risks.append({
            "id": "R3",
            "category": "resources",
            "description": "Limited resources may cause bottlenecks",
            "severity": "low",
            "probability": 0.3,
            "impact": "Single point of failure, knowledge gaps",
        })
    
    # Action-specific risks
    for i, action in enumerate(actions[:5]):
        action_text = action.get("action", "") if isinstance(action, dict) else str(action)
        if any(kw in action_text.lower() for kw in ["integrate", "migrate", "deploy"]):
            risks.append({
                "id": f"R{i+10}",
                "category": "technical",
                "description": f"Action '{action_text[:50]}' involves technical change",
                "severity": "medium",
                "probability": 0.5,
                "impact": "Potential system disruption",
            })
    
    # Calculate overall risk level
    severity_scores = {"low": 1, "medium": 2, "high": 3}
    if not risks:
        overall_risk = "low"
    else:
        avg_severity = sum(severity_scores.get(r.get("severity", "low"), 1) for r in risks) / len(risks)
        overall_risk = "low" if avg_severity < 1.5 else "medium" if avg_severity < 2.5 else "high"
    
    # Generate mitigations
    mitigations = []
    if overall_risk in ["medium", "high"]:
        mitigations.append("Break down complex tasks into smaller, manageable pieces")
        mitigations.append("Set up regular check-ins to monitor progress")
        mitigations.append("Prepare rollback plan for high-risk actions")
    if any(r.get("category") == "resources" for r in risks):
        mitigations.append("Identify backup resources or cross-train team members")
    if any(r.get("category") == "technical" for r in risks):
        mitigations.append("Test changes in staging environment first")
    
    # Determine if approval is required
    approval_required = overall_risk in ["medium", "high"] or len(risks) >= 3
    
    return {
        "overall_risk_level": overall_risk,
        "risks": risks,
        "mitigations": mitigations,
        "approval_required": approval_required,
        "risk_score": sum(severity_scores.get(r.get("severity", "low"), 1) for r in risks),
        "assessed_at": datetime.now(timezone.utc).isoformat(),
    }
