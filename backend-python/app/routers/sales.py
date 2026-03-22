from fastapi import APIRouter

router = APIRouter(prefix="/sales", tags=["sales"])


@router.get("/leads")
async def leads():
    return {"data": []}


@router.get("/pipeline")
async def pipeline():
    return {"data": []}


@router.get("/discover")
async def discover():
    return {"data": []}


@router.get("/invoices")
async def invoices():
    return {"data": []}


@router.get("/payments")
async def payments():
    return {"data": []}
