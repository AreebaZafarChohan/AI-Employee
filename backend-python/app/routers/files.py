from fastapi import APIRouter

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/pending")
async def pending():
    return {"data": []}


@router.get("/stats")
async def stats():
    return {"data": {"total": 0, "pending": 0, "processed": 0}}
