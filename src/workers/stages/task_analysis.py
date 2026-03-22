"""
Task Analysis Stage Worker

This is the first stage of the 4-stage pipeline.
It parses the task description, extracts requirements, and identifies key entities.

Input: Job with task_description
Output: Structured task analysis with requirements, entities, and domain
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
    Task Analysis Stage: Parse task and extract requirements.
    
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
        
        job_uuid = UUID(job_id)
        db: Session = next(get_db_session())
        
        try:
            # Get job details
            job = db.query(Job).filter(Job.id == job_uuid).first()
            if not job:
                raise ValueError(f"Job not found: {job_id}")
            
            # Create pipeline stage record
            stage = PipelineStage(
                job_id=job_uuid,
                stage_type="task_analysis",
                status=PipelineStageStatus.RUNNING,
                input_data={"task_description": job.task_description},
                started_at=datetime.now(timezone.utc),
                timeout_seconds=30,
            )
            db.add(stage)
            db.commit()
            stage_id = stage.id
            
            logger.info(f"Task analysis started for job {job_id}")
            publish_event(EventType.STAGE_STARTED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "task_analysis",
            })
            
            # Perform task analysis (AI-powered parsing)
            # In production, this would call an AI model
            analysis_result = _analyze_task(job.task_description)
            
            # Update progress
            publish_progress(job_uuid, 25, "task_analysis")
            
            # Store output
            stage.output_data = analysis_result
            stage.status = PipelineStageStatus.COMPLETED
            stage.completed_at=datetime.now(timezone.utc)
            db.commit()
            
            logger.info(f"Task analysis completed for job {job_id}")
            publish_event(EventType.STAGE_COMPLETED, {
                "job_id": job_id,
                "stage_id": str(stage_id),
                "stage_type": "task_analysis",
                "progress": 25,
                "output": analysis_result,
            })
            
            # Trigger next stage: Plan Creation
            from src.workers.stages.plan_creation import process as plan_creation
            plan_creation.delay(job_id)
            
            return {"status": "completed", "stage_id": str(stage_id), "analysis": analysis_result}
            
        finally:
            db.close()
    
    except Exception as e:
        logger.error(f"Task analysis failed for job {job_id}: {e}", exc_info=True)
        
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
            "stage_type": "task_analysis",
            "error": str(e),
            "retry_count": self.request.retries,
        })
        
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


def _analyze_task(task_description: str) -> dict:
    """
    Analyze task description and extract structured information.
    
    In production, this would use AI/LLM to parse the task.
    For now, we use basic NLP heuristics.
    
    Returns:
        dict with:
            - summary: Brief task summary
            - requirements: List of identified requirements
            - entities: Key entities mentioned
            - domain: Identified domain (e.g., 'sales', 'engineering')
            - complexity: Estimated complexity (low/medium/high)
    """
    # Basic analysis (replace with AI in production)
    text = task_description.lower()
    
    # Identify domain keywords
    domain_keywords = {
        "sales": ["sell", "customer", "revenue", "lead", "prospect", "deal"],
        "engineering": ["build", "develop", "code", "api", "system", "feature"],
        "marketing": ["campaign", "brand", "audience", "content", "social"],
        "support": ["help", "issue", "bug", "ticket", "customer service"],
    }
    
    domain = "general"
    max_matches = 0
    for d, keywords in domain_keywords.items():
        matches = sum(1 for k in keywords if k in text)
        if matches > max_matches:
            domain = d
            max_matches = matches
    
    # Estimate complexity based on length and keywords
    complexity = "low"
    if len(task_description) > 200 or any(w in text for w in ["complex", "multiple", "integrate"]):
        complexity = "medium"
    if len(task_description) > 500 or any(w in text for w in ["enterprise", "scale", "critical"]):
        complexity = "high"
    
    # Extract potential requirements (sentences starting with action verbs)
    sentences = task_description.replace(".", "\n").replace("!", "\n").split("\n")
    requirements = [
        s.strip() for s in sentences 
        if len(s.strip()) > 10 and any(
            s.strip().lower().startswith(v) 
            for v in ["create", "build", "implement", "add", "fix", "update", "design"]
        )
    ]
    
    return {
        "summary": task_description[:200] + ("..." if len(task_description) > 200 else ""),
        "requirements": requirements[:10],  # Limit to 10
        "entities": [],  # Would be extracted by AI in production
        "domain": domain,
        "complexity": complexity,
        "word_count": len(task_description.split()),
        "estimated_effort": "1-2 hours" if complexity == "low" else "2-4 hours" if complexity == "medium" else "4+ hours",
    }
