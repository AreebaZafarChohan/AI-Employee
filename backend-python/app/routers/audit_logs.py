from fastapi import APIRouter, Query
from datetime import datetime, timezone
from app.services import audit_service

router = APIRouter(prefix="/audit-logs", tags=["audit"])


@router.get("")
async def get_audit_logs(limit: int = Query(100, le=500), source: str = Query("all")):
    entries = audit_service.get_audit_logs(limit=limit, source=source)
    return {
        "data": entries,
        "meta": {"total": len(entries), "limit": limit, "source": source, "timestamp": datetime.now(timezone.utc).isoformat()},
    }


@router.get("/activity")
async def get_activity_logs(limit: int = Query(100, le=500)):
    """Get unified activity logs from all sources (Gmail, WhatsApp, Vault, Orchestrator, LEX)"""
    entries = audit_service.get_unified_activity_logs(limit=limit)
    return {
        "data": entries,
        "meta": {"total": len(entries), "limit": limit, "timestamp": datetime.now(timezone.utc).isoformat()},
    }
