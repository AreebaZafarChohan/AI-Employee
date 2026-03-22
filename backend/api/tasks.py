from fastapi import APIRouter
from backend.api.response import api_response
from backend.api.vault_utils import read_vault_folder

router = APIRouter(prefix="/tasks", tags=["Tasks"])

@router.get("/pending")
async def get_pending():
    return api_response(read_vault_folder("Pending_Approval"))

@router.get("/needs-action")
async def get_needs_action():
    return api_response(read_vault_folder("Needs_Action"))

@router.get("/done")
async def get_done():
    return api_response(read_vault_folder("Done"))
