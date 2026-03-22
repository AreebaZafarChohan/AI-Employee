from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timezone

from app.services.watcher_service import get_watcher_service

router = APIRouter(prefix="/watchers", tags=["watchers"])


@router.get("")
async def list_watchers():
    """List all watchers with their current status."""
    service = get_watcher_service()
    watchers = service.list_watchers()
    return {"data": watchers, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.get("/summary")
async def get_service_summary():
    """Get summary statistics for all watchers."""
    service = get_watcher_service()
    summary = service.get_service_summary()
    return {"data": summary, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.get("/{watcher_id}")
async def get_watcher_status(watcher_id: str):
    """Get status of a specific watcher."""
    service = get_watcher_service()
    status = service.get_watcher_status(watcher_id)
    
    if not status:
        raise HTTPException(status_code=404, detail=f"Watcher {watcher_id} not found")
    
    return {"data": status, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.post("/{watcher_id}/start")
async def start_watcher(watcher_id: str):
    """Start a watcher process."""
    service = get_watcher_service()
    result = service.start_watcher(watcher_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to start watcher"))
    
    return {"data": result, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.post("/{watcher_id}/stop")
async def stop_watcher(watcher_id: str):
    """Stop a watcher process."""
    service = get_watcher_service()
    result = service.stop_watcher(watcher_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to stop watcher"))
    
    return {"data": result, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.post("/{watcher_id}/restart")
async def restart_watcher(watcher_id: str):
    """Restart a watcher process."""
    service = get_watcher_service()
    result = service.restart_watcher(watcher_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Failed to restart watcher"))
    
    return {"data": result, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.get("/{watcher_id}/logs")
async def get_watcher_logs(
    watcher_id: str,
    limit: Optional[int] = Query(default=100, ge=1, le=1000, description="Number of log entries to retrieve"),
):
    """Get recent logs for a watcher."""
    service = get_watcher_service()
    logs = service.get_watcher_logs(watcher_id, limit)
    return {"data": logs, "meta": {"timestamp": datetime.now(timezone.utc).isoformat(), "count": len(logs)}}


@router.post("/start-all")
async def start_all_watchers():
    """Start all available watchers."""
    service = get_watcher_service()
    result = service.start_all_watchers()
    return {"data": result, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.post("/stop-all")
async def stop_all_watchers():
    """Stop all running watchers."""
    service = get_watcher_service()
    result = service.stop_all_watchers()
    return {"data": result, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}


@router.get("/registry/list")
async def list_watcher_registry():
    """List all available watchers in the registry (including those without scripts)."""
    service = get_watcher_service()
    registry = service.WATCHER_REGISTRY
    return {"data": registry, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}
