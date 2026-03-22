from fastapi import APIRouter
from pydantic import BaseModel
from backend.api.response import api_response
from backend.api.vault_utils import read_vault_folder

router = APIRouter(prefix="/vault", tags=["Vault"])

class ApproveRejectInput(BaseModel):
    filename: str

@router.get("/counts")
async def get_counts():
    return api_response({
        "pending": len(read_vault_folder("Pending_Approval")),
        "needs-action": len(read_vault_folder("Needs_Action")),
        "done": len(read_vault_folder("Done"))
    })

@router.get("/inbox")
async def get_inbox():
    return api_response(read_vault_folder("Inbox"))

@router.get("/needs-action")
async def get_needs_action():
    return api_response(read_vault_folder("Needs_Action"))

@router.get("/pending")
async def get_pending():
    return api_response(read_vault_folder("Pending_Approval"))

@router.get("/done")
async def get_done():
    return api_response(read_vault_folder("Done"))

@router.post("/approve")
async def approve(body: ApproveRejectInput):
    return api_response({"status": "approved", "file": body.filename})

@router.post("/reject")
async def reject(body: ApproveRejectInput):
    return api_response({"status": "rejected", "file": body.filename})
