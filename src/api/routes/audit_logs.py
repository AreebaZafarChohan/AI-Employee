"""Audit logs router - reads from vault Audit/ folder."""

from fastapi import APIRouter, Query
from src.api.response import api_response
from src.api.vault_utils import read_vault_folder

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])


@router.get("")
async def list_audit_logs(limit: int = Query(50, ge=1, le=500)):
    items = read_vault_folder("Audit")
    # Sort by date descending, take limit
    items.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
    return api_response(items[:limit], meta={"total": len(items)})
