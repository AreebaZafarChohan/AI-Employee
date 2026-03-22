"""Gmail router - inbox and message detail."""

from fastapi import APIRouter, HTTPException
from src.api.response import api_response

router = APIRouter(prefix="/gmail", tags=["Gmail"])


@router.get("/inbox")
async def get_inbox():
    return api_response([])


@router.get("/message/{message_id}")
async def get_message(message_id: str):
    return api_response({
        "id": message_id,
        "subject": "",
        "from": "",
        "body": "",
        "date": None,
    })
