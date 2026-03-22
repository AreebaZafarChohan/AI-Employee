"""Events router for Watcher integration."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from src.api.response import api_response
from src.core.event_queue import event_queue

router = APIRouter(prefix="/events", tags=["Watcher Events"])

class WatcherEventInput(BaseModel):
    source: str
    file: str
    metadata: Dict[str, Any] = {}

@router.post("/new")
async def push_watcher_event(body: WatcherEventInput):
    """Notify the backend of a new item detected by a watcher."""
    try:
        event_data = {
            "source": body.source,
            "file": body.file,
            "metadata": body.metadata
        }
        
        # Async push to event queue
        await event_queue.push_event(event_data)
        
        return api_response({
            "status": "queued",
            "source": body.source,
            "file": body.file
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
