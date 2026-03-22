from fastapi import APIRouter
from datetime import datetime, timezone
from app.services import mcp_service

router = APIRouter(prefix="/system", tags=["mcp"])


@router.get("/mcp-health")
async def mcp_health():
    data = mcp_service.get_mcp_health()
    return {"data": data, "meta": {"timestamp": datetime.now(timezone.utc).isoformat()}}
