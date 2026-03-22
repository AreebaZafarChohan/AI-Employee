"""
Plan Creation Stage Worker

This is the second stage of the 4-stage pipeline.
It generates a structured plan with recommended actions based on the task analysis.

Input: Task analysis output from stage 1
Output: Structured plan with recommended actions, timeline, and resources
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
    Plan Creation Stage: Generate structured plan from task analysis.
    
    Args:
        job_id: The job UUID as string
    """
    stage_id = None
    
    try:
        from sqlalchemy.orm import Session
        from src.models.base import get_db_session
        from src.models.pipeline_stage import PipelineStage
        from src.models.enums import PipelineStageStatus
        from src.models.job import Job
        from src.models.plan import Plan
        
        job_uuid = UUID(job_id)
        db: Session = next(get_db_session())
        
        try:
            # Get the task analysis output from previous stage
            analysis_stage = db.query(PipelineStage).filter(
                PipelineStage.job_id == job_uuid,
                PipelineStage.stage_type == "task_analysis",
                PipelineStage.status == PipelineStageStatus.COMPLETED,
            ).first()
            
            if not analysis_stage:
                raise ValueError(f"Task analysis not found for job {job_id}")
            
            analysis = analysis_stage.output_data or {}
            
            # Create pipeline stage record
            stage = PipelineStage(
                job_id=job_uuid,
                stage_type="plan_creation",
                status=PipelineStageStatus.RUNNING,
                input_data={"analysis": analysis},
                started_at=datetime.now(timezone.utc),
                timeout_seconds=30,
            )
            db.add(stage)
            db.commit()
            stage_id = stage.id
            
            logger.info(f"Plan creation started for job {job_id}")
            publish_event(EventType.STAGE_STARTED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "plan_creation",
            })
            
            # Generate plan (AI-powered)
            plan_result = _generate_plan(analysis)
            
            # Update progress
            publish_progress(job_uuid, 50, "plan_creation")
            
            # Create Plan record
            plan = Plan(
                job_id=job_uuid,
                version=1,
                task_analysis=analysis,
                recommended_actions=plan_result.get("recommended_actions", []),
                risk_assessment=None,  # Will be filled by next stage
                approval_status="pending",
            )
            db.add(plan)
            
            # Store output
            stage.output_data = plan_result
            stage.status = PipelineStageStatus.COMPLETED
            stage.completed_at=datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Plan creation completed for job {job_id}")
            publish_event(EventType.STAGE_COMPLETED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "plan_creation",
                "progress": 50,
                "output": plan_result,
            })
            
            # Trigger next stage: Risk Assessment
            from src.workers.stages.risk_assessment import process as risk_assessment
            risk_assessment.delay(job_id)
            
            return {"status": "completed", "stage_id": str(stage_id), "plan": plan_result}
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Plan creation failed for job {job_id}: {e}", exc_info=True)
        
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
            "stage_type": "plan_creation",
            "error": str(e),
            "retry_count": self.request.retries,
        })
        
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


def _generate_plan(analysis: dict) -> dict:
    """
    Generate a structured plan based on task analysis.
    
    In production, this would use AI/LLM to generate the plan.
    For now, we use template-based generation.
    
    Returns:
        dict with:
            - objectives: Clear objectives to achieve
            - recommended_actions: Ordered list of actions
            - timeline: Estimated timeline
            - resources: Required resources
            - success_criteria: How to measure success
    """
    domain = analysis.get("domain", "general")
    complexity = analysis.get("complexity", "medium")
    requirements = analysis.get("requirements", [])
    
    # Generate recommended actions based on domain
    action_templates = {
        "sales": [
            "Identify target customer segment",
            "Prepare value proposition",
            "Create outreach strategy",
            "Set up tracking and metrics",
        ],
        "engineering": [
            "Define technical requirements",
            "Design system architecture",
            "Implement core functionality",
            "Write tests and documentation",
        ],
        "marketing": [
            "Define target audience",
            "Create content strategy",
            "Set up campaign channels",
            "Measure and optimize performance",
        ],
        "support": [
            "Categorize and prioritize issues",
            "Develop resolution procedures",
            "Create knowledge base articles",
            "Implement feedback loop",
        ],
    }
    
    base_actions = action_templates.get(domain, [
        "Analyze requirements in detail",
        "Design solution approach",
        "Implement solution",
        "Validate and document",
    ])
    
    # Adjust based on complexity
    if complexity == "high":
        base_actions.insert(0, "Conduct stakeholder alignment")
        base_actions.append("Plan rollback strategy")
    
    # Build timeline estimate
    timeline_map = {
        "low": "1-2 days",
        "medium": "3-5 days",
        "high": "1-2 weeks",
    }
    
    return {
        "objectives": requirements[:3] if requirements else ["Complete the requested task"],
        "recommended_actions": [
            {"order": i + 1, "action": action, "status": "pending"}
            for i, action in enumerate(base_actions)
        ],
        "timeline": timeline_map.get(complexity, "3-5 days"),
        "resources": ["AI Assistant", "Domain Expert (if needed)"],
        "success_criteria": [
            "All requirements addressed",
            "Quality standards met",
            "Delivered within timeline",
        ],
        "domain": domain,
        "complexity": complexity,
    }
