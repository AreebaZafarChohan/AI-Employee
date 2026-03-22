from fastapi import APIRouter
from app.services import vault_service

router = APIRouter(prefix="/approvals", tags=["approvals"])


@router.get("/metrics")
async def approval_metrics():
    counts = vault_service.get_counts()
    return {"data": {
        "pending": counts.get("pending", 0),
        "approved": counts.get("approved", 0),
        "rejected": counts.get("rejected", 0),
        "total": sum(counts.values()),
    }}
