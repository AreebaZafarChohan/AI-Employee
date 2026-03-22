"""Social Media router for post generation."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from src.api.response import api_response
from src.services.social_service import generate_social_post

from src.api.vault_utils import read_vault_folder, move_vault_file

router = APIRouter(prefix="/social", tags=["Social Media"])


class GeneratePostInput(BaseModel):
    platform: str
    topic: str


@router.post("/generate")
async def generate_post(body: GeneratePostInput):
    """Generate a social media post and save it as pending."""
    result = generate_social_post(body.topic, body.platform)
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return api_response(result)


@router.get("/drafts")
async def get_social_drafts():
    """Get all social post drafts from Pending_Approval."""
    pending = read_vault_folder("Pending_Approval")
    drafts = [item for item in pending if item.get("type") == "social_post" or "POST_" in item.get("filename", "")]
    return api_response(drafts)


@router.get("/platforms")
async def list_platforms():
    """List available platforms for post generation."""
    platforms = [
        {"id": "linkedin", "name": "LinkedIn"},
        {"id": "facebook", "name": "Facebook"},
        {"id": "twitter", "name": "Twitter/X"},
        {"id": "instagram", "name": "Instagram"},
        {"id": "whatsapp", "name": "WhatsApp (Outbound)"},
    ]
    return api_response(platforms)
