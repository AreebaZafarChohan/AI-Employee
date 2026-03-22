"""Vault router - needs-action, pending, approved, rejected, done, counts, approve/reject."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.response import api_response
from src.api.vault_utils import read_vault_folder, move_vault_file

router = APIRouter(prefix="/vault", tags=["Vault"])

FOLDER_MAP = {
    "needs-action": "Needs_Action",
    "pending": "Pending_Approval",
    "approved": "Approved",
    "rejected": "Rejected",
    "done": "Done",
}


@router.get("/needs-action")
async def get_needs_action():
    return api_response(read_vault_folder("Needs_Action"))


@router.get("/pending")
async def get_pending():
    return api_response(read_vault_folder("Pending_Approval"))


@router.get("/approved")
async def get_approved():
    return api_response(read_vault_folder("Approved"))


@router.get("/rejected")
async def get_rejected():
    return api_response(read_vault_folder("Rejected"))


@router.get("/done")
async def get_done():
    return api_response(read_vault_folder("Done"))


@router.get("/counts")
async def get_counts():
    counts = {}
    for key, folder in FOLDER_MAP.items():
        counts[key] = len(read_vault_folder(folder))
    return api_response(counts)


@router.get("/approvals")
async def get_approvals():
    """Consolidated approvals view (Pending_Approval + Needs_Action)."""
    pending = read_vault_folder("Pending_Approval")
    needs_action = read_vault_folder("Needs_Action")
    return api_response(pending + needs_action)

@router.get("/logs")
async def get_logs():
    """Daily logs from /Logs."""
    return api_response(read_vault_folder("Logs"))

@router.get("/inbox")
async def get_inbox():
    """Incoming items from /Inbox."""
    return api_response(read_vault_folder("Inbox"))

class ApproveRejectInput(BaseModel):
    filename: str


@router.post("/approve")
async def approve_file(body: ApproveRejectInput):
    # Try to move from Pending_Approval to Approved
    result = move_vault_file(body.filename, "Pending_Approval", "Approved")
    if not result:
        # Also try from Needs_Action
        result = move_vault_file(body.filename, "Needs_Action", "Approved")
    if not result:
        raise HTTPException(status_code=404, detail=f"File '{body.filename}' not found in pending or needs-action")
    return api_response({"filename": body.filename, "status": "approved", "path": result})


@router.post("/reject")
async def reject_file(body: ApproveRejectInput):
    result = move_vault_file(body.filename, "Pending_Approval", "Rejected")
    if not result:
        result = move_vault_file(body.filename, "Needs_Action", "Rejected")
    if not result:
        raise HTTPException(status_code=404, detail=f"File '{body.filename}' not found in pending or needs-action")
    return api_response({"filename": body.filename, "status": "rejected", "path": result})
