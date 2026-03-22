"""Files router - pending files, stats, approve/reject."""

from pathlib import Path
from fastapi import APIRouter, HTTPException
from src.api.response import api_response
from src.api.vault_utils import read_vault_folder

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/pending")
async def get_pending_files():
    return api_response(read_vault_folder("Pending_Approval"))


@router.get("/stats")
async def get_file_stats():
    pending = len(read_vault_folder("Pending_Approval"))
    approved = len(read_vault_folder("Approved"))
    rejected = len(read_vault_folder("Rejected"))
    return api_response({
        "pending": pending,
        "approved": approved,
        "rejected": rejected,
        "total": pending + approved + rejected,
    })


@router.get("/{file_path:path}")
async def get_file(file_path: str):
    """Read a specific file by path from the vault."""
    from src.core.config import get_settings
    settings = get_settings()
    full = Path(settings.VAULT_PATH) / file_path
    if not full.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    content = full.read_text(encoding="utf-8", errors="replace")
    return api_response({"path": file_path, "content": content, "name": full.name})


@router.post("/{file_path:path}/approve")
async def approve_file(file_path: str):
    from src.api.vault_utils import move_vault_file
    filename = Path(file_path).name
    result = move_vault_file(filename, "Pending_Approval", "Approved")
    if not result:
        raise HTTPException(status_code=404, detail="File not found in pending")
    return api_response({"filename": filename, "status": "approved"})


@router.post("/{file_path:path}/reject")
async def reject_file(file_path: str):
    from src.api.vault_utils import move_vault_file
    filename = Path(file_path).name
    result = move_vault_file(filename, "Pending_Approval", "Rejected")
    if not result:
        raise HTTPException(status_code=404, detail="File not found in pending")
    return api_response({"filename": filename, "status": "rejected"})
