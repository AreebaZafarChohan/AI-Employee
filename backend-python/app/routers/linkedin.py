from fastapi import APIRouter

router = APIRouter(prefix="/linkedin", tags=["linkedin"])


@router.get("/connections")
async def connections():
    return {"data": []}


@router.get("/messages")
async def messages():
    return {"data": []}


@router.get("/posts")
async def posts():
    return {"data": []}


@router.get("/status")
async def status():
    return {"data": {"connected": False, "status": "not_configured"}}
