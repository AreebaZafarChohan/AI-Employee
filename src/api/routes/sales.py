"""Sales router - leads, pipeline, invoices, payments, discover."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from src.api.response import api_response

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.get("/leads")
async def get_leads():
    return api_response([])


@router.get("/leads/{lead_id}")
async def get_lead(lead_id: str):
    return api_response({"id": lead_id, "name": "", "status": "new"})


@router.get("/pipeline")
async def get_pipeline():
    return api_response({
        "stages": [
            {"name": "Prospecting", "count": 0, "value": 0},
            {"name": "Qualification", "count": 0, "value": 0},
            {"name": "Proposal", "count": 0, "value": 0},
            {"name": "Negotiation", "count": 0, "value": 0},
            {"name": "Closed Won", "count": 0, "value": 0},
        ]
    })


@router.get("/invoices")
async def get_invoices():
    return api_response([])


@router.get("/payments")
async def get_payments():
    return api_response([])


class DiscoverInput(BaseModel):
    query: Optional[str] = None


@router.post("/discover")
async def discover_leads(body: DiscoverInput):
    return api_response({"discovered": 0, "leads": []})
