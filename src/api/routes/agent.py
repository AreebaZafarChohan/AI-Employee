"""Agent router for handling natural language commands."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.api.response import api_response
from src.core.command_router import command_router

router = APIRouter(prefix="/agent", tags=["AI Agent"])

class CommandInput(BaseModel):
    command: str

@router.post("/command")
async def process_command(body: CommandInput):
    """Send a natural language command to the AI agent."""
    try:
        result = command_router.process_command(body.command)
        return api_response(result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_agent_status():
    """Get status of the agent loops and vault queues."""
    # This could be expanded to check if ralph_loop.py is running
    return api_response({
        "status": "active",
        "loops": ["ralph_loop"],
        "orchestrators": ["approval_orchestrator"]
    })
