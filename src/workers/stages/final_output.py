"""
Final Output Stage Worker

This is the fourth and final stage of the 4-stage pipeline.
It assembles all outputs into a complete deliverable and marks the job as complete.

Input: All previous stage outputs
Output: Complete job output ready for human approval
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
    Final Output Stage: Assemble complete deliverable and finalize job.
    
    Args:
        job_id: The job UUID as string
    """
    stage_id = None
    
    try:
        from sqlalchemy.orm import Session
        from src.models.base import get_db_session
        from src.models.pipeline_stage import PipelineStage
        from src.models.enums import PipelineStageStatus, JobStatus
        from src.models.job import Job
        from src.models.plan import Plan
        
        job_uuid = UUID(job_id)
        db: Session = next(get_db_session())
        
        try:
            # Gather all previous stage outputs
            stages = db.query(PipelineStage).filter(
                PipelineStage.job_id == job_uuid,
                PipelineStage.stage_type.in_(["task_analysis", "plan_creation", "risk_assessment"]),
            ).all()
            
            if len(stages) < 3:
                raise ValueError(f"Incomplete pipeline for job {job_id}: only {len(stages)} stages found")
            
            # Build stage outputs map
            stage_outputs = {}
            for stage in stages:
                stage_outputs[stage.stage_type.value] = stage.output_data
            
            # Get the plan
            plan = db.query(Plan).filter(Plan.job_id == job_uuid).first()
            if not plan:
                raise ValueError(f"Plan not found for job {job_id}")
            
            # Create pipeline stage record
            stage = PipelineStage(
                job_id=job_uuid,
                stage_type="final_output",
                status=PipelineStageStatus.RUNNING,
                input_data={"stage_outputs": stage_outputs},
                started_at=datetime.now(timezone.utc),
                timeout_seconds=30,
            )
            db.add(stage)
            db.commit()
            stage_id = stage.id
            
            logger.info(f"Final output assembly started for job {job_id}")
            publish_event(EventType.STAGE_STARTED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "final_output",
            })
            
            # Assemble final output
            final_output = _assemble_final_output(stage_outputs, plan)
            
            # Update progress
            publish_progress(job_uuid, 90, "final_output")
            
            # Store output
            stage.output_data = final_output
            stage.status = PipelineStageStatus.COMPLETED
            stage.completed_at=datetime.now(timezone.utc)
            
            # Update job status
            job = db.query(Job).filter(Job.id == job_uuid).first()
            if job:
                job.status = JobStatus.PENDING_APPROVAL
                job.progress_percentage = 100
                job.completed_at = datetime.now(timezone.utc)
            
            # Update plan approval status
            plan.approval_status = "pending"
            
            db.commit()
            
            logger.info(f"Final output completed for job {job_id}")
            publish_event(EventType.STAGE_COMPLETED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "final_output",
                "progress": 100,
                "output": final_output,
            })
            
            # Job complete - trigger approval workflow
            publish_event(EventType.JOB_COMPLETED, {
                "job_id": job_id,
                "plan_id": str(plan.id),
                "duration_ms": 0,  # Would calculate from job start time
            })
            
            # Notify for approval
            publish_event(EventType.PLAN_PENDING_APPROVAL, {
                "job_id": job_id,
                "plan_id": str(plan.id),
                "risk_level": stage_outputs.get("risk_assessment", {}).get("overall_risk_level", "unknown"),
            })
            
            return {"status": "completed", "stage_id": str(stage_id), "output": final_output}
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Final output assembly failed for job {job_id}: {e}", exc_info=True)
        
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
        
        # Update job status to failed
        try:
            db: Session = next(get_db_session())
            job = db.query(Job).filter(Job.id == job_uuid).first()
            if job:
                job.status = JobStatus.FAILED
                db.commit()
            db.close()
        except Exception:
            pass
        
        publish_event(EventType.JOB_FAILED, {
            "job_id": job_id,
            "error": str(e),
        })
        
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


def _assemble_final_output(stage_outputs: dict, plan) -> dict:
    """
    Assemble all stage outputs into a complete deliverable.
    
    Returns:
        dict with complete job output including:
            - summary: Executive summary
            - task_analysis: From stage 1
            - plan: From stage 2
            - risk_assessment: From stage 3
            - recommendations: Final recommendations
            - approval_required: Boolean
    """
    analysis = stage_outputs.get("task_analysis", {})
    plan_data = stage_outputs.get("plan_creation", {})
    risks = stage_outputs.get("risk_assessment", {})
    
    # Build executive summary
    summary_parts = []
    if analysis.get("summary"):
        summary_parts.append(f"Task: {analysis['summary'][:100]}...")
    if analysis.get("domain"):
        summary_parts.append(f"Domain: {analysis['domain']}")
    if analysis.get("complexity"):
        summary_parts.append(f"Complexity: {analysis['complexity']}")
    
    actions = plan_data.get("recommended_actions", [])
    if actions:
        summary_parts.append(f"Action plan: {len(actions)} steps identified")
    
    risk_level = risks.get("overall_risk_level", "unknown")
    if risk_level:
        summary_parts.append(f"Risk level: {risk_level}")
    
    # Build final recommendations
    recommendations = []
    if risks.get("approval_required"):
        recommendations.append("Human approval required before proceeding")
    if risks.get("mitigations"):
        recommendations.append(f"Implement {len(risks['mitigations'])} risk mitigations")
    if plan_data.get("timeline"):
        recommendations.append(f"Follow estimated timeline: {plan_data['timeline']}")
    
    return {
        "summary": " | ".join(summary_parts),
        "task_analysis": analysis,
        "plan": {
            "objectives": plan_data.get("objectives", []),
            "recommended_actions": actions,
            "timeline": plan_data.get("timeline"),
            "resources": plan_data.get("resources", []),
        },
        "risk_assessment": risks,
        "recommendations": recommendations,
        "approval_required": risks.get("approval_required", True),
        "assembled_at": datetime.now(timezone.utc).isoformat(),
        "pipeline_version": "1.0",
    }
