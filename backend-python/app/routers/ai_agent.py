from fastapi import APIRouter
from pydantic import BaseModel
from app.services import ai_agent_service

router = APIRouter(prefix="/ai-agent", tags=["ai-agent"])


@router.get("/status")
async def status():
    return {"data": {"status": "ready", "providers": ["gemini"]}}


class GenerateRequest(BaseModel):
    prompt: str
    provider: str = "gemini"


@router.post("/generate")
async def generate(body: GenerateRequest):
    result = await ai_agent_service.generate_content(body.prompt, body.provider)
    return {"data": result}


@router.get("/history")
async def history():
    return {"data": []}
