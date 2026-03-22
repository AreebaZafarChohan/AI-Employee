from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services import vault_service

router = APIRouter(prefix="/vault", tags=["vault"])


@router.get("/needs-action")
async def needs_action():
    return {"data": vault_service.get_folder_items("needs_action")}


@router.get("/pending")
async def pending():
    return {"data": vault_service.get_folder_items("pending")}


@router.get("/approved")
async def approved():
    return {"data": vault_service.get_folder_items("approved")}


@router.get("/rejected")
async def rejected():
    return {"data": vault_service.get_folder_items("rejected")}


@router.get("/done")
async def done():
    return {"data": vault_service.get_folder_items("done")}


@router.get("/counts")
async def counts():
    return {"data": vault_service.get_counts()}


class FileAction(BaseModel):
    filename: str


@router.post("/approve")
async def approve(body: FileAction):
    result = vault_service.move_file(body.filename, ["Pending_Approval", "Needs_Action"], "Approved")
    if not result:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "File not found"})
    return {"data": {"success": True, "message": "File approved", "filename": body.filename, "new_status": "approved"}}


@router.post("/reject")
async def reject(body: FileAction):
    result = vault_service.move_file(body.filename, ["Pending_Approval", "Needs_Action"], "Rejected")
    if not result:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "File not found"})
    return {"data": {"success": True, "message": "File rejected", "filename": body.filename, "new_status": "rejected"}}
