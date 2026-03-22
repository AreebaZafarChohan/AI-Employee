"""LinkedIn router - connections, messages, posts, status."""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from src.api.response import api_response

router = APIRouter(prefix="/linkedin", tags=["LinkedIn"])


@router.get("/connections")
async def get_connections():
    return api_response([])


@router.get("/messages")
async def get_messages():
    return api_response([])


@router.get("/posts")
async def get_posts():
    return api_response([])


@router.get("/status")
async def get_status():
    return api_response({"connected": False, "lastSync": None})


class CreatePostInput(BaseModel):
    content: str
    visibility: Optional[str] = "public"


@router.post("/posts")
async def create_post(body: CreatePostInput):
    return api_response({"posted": False, "reason": "LinkedIn integration not configured"})
