from fastapi import APIRouter
from pydantic import BaseModel
from backend.api.response import api_response

router = APIRouter(prefix="/events", tags=["Watcher Events"])

class EventInput(BaseModel):
    source: str
    file: str

@router.post("/new")
async def notify_new_event(body: EventInput):
    return api_response({"status": "queued", "source": body.source, "file": body.file})
