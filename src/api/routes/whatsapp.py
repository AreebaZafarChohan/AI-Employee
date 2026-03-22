"""WhatsApp router - messages, status, send."""

from fastapi import APIRouter
from pydantic import BaseModel
from src.api.response import api_response

router = APIRouter(prefix="/whatsapp", tags=["WhatsApp"])


@router.get("/messages")
async def get_messages():
    return api_response([])


@router.get("/status")
async def get_status():
    return api_response({"connected": False, "lastSync": None})


class SendMessageInput(BaseModel):
    to: str
    message: str


@router.post("/send")
async def send_message(body: SendMessageInput):
    # Placeholder - will integrate with WhatsApp MCP server
    return api_response({"sent": False, "reason": "WhatsApp integration not configured"})
