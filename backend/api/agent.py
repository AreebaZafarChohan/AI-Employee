from fastapi import APIRouter
from pydantic import BaseModel
from backend.api.response import api_response
from backend.ai_router import generate

router = APIRouter(prefix="/agent", tags=["AI Agent"])

class CommandInput(BaseModel):
    command: str

@router.post("/command")
async def process_command(body: CommandInput):
    # For dev setup, just return success
    return api_response({
        "status": "success",
        "message": f"Command received: {body.command}",
        "task_id": "task-123"
    })
