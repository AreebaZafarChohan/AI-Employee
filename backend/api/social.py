from fastapi import APIRouter
from backend.api.response import api_response
from backend.api.vault_utils import read_vault_folder

router = APIRouter(prefix="/social", tags=["Social Media"])

@router.get("/drafts")
async def get_drafts():
    pending = read_vault_folder("Pending_Approval")
    drafts = [item for item in pending if "POST_" in item.get("filename", "")]
    return api_response(drafts)
