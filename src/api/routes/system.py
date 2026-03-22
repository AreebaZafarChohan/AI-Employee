"""System state, health, and MCP health router."""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.models.sqlite_db import get_db
from src.models.dashboard_models import SystemState
from src.api.response import api_response

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/state")
async def get_system_state(db: Session = Depends(get_db)):
    row = db.query(SystemState).filter(SystemState.id == "main").first()
    if not row:
        return api_response({
            "id": "main",
            "state": "idle",
            "lastActivity": datetime.now(timezone.utc).isoformat(),
            "updatedAt": datetime.now(timezone.utc).isoformat(),
        })
    return api_response(row.to_dict())


@router.get("/health")
async def system_health():
    return api_response({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {
            "database": "connected",
            "vault": "available",
        },
    })


@router.get("/mcp-health")
async def mcp_health():
    """Check MCP server health. Returns status for each configured server."""
    import httpx

    servers = {
        "odoo": "http://localhost:3001/health",
        "twitter": "http://localhost:3002/health",
        "facebook": "http://localhost:3003/health",
        "instagram": "http://localhost:3004/health",
    }
    results = {}
    async with httpx.AsyncClient(timeout=3.0) as client:
        for name, url in servers.items():
            try:
                resp = await client.get(url)
                results[name] = {
                    "status": "healthy" if resp.status_code == 200 else "unhealthy",
                    "statusCode": resp.status_code,
                }
            except Exception:
                results[name] = {"status": "unreachable", "statusCode": None}
    return api_response(results)
