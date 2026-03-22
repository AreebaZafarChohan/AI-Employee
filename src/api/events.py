"""Event broadcast helpers."""

import logging
from src.api.websocket_manager import manager

logger = logging.getLogger("api_events")

async def broadcast_event(event_type: str, data: dict):
    """Broadcast an event to all connected UI clients."""
    message = {
        "type": event_type,
        "payload": data
    }
    await manager.broadcast(message)

async def notify_new_task(task_id: str, title: str):
    await broadcast_event("task_created", {"id": task_id, "title": title})

async def notify_new_draft(filename: str, type: str):
    await broadcast_event("draft_generated", {"filename": filename, "type": type})

async def notify_approval_required(filename: str):
    await broadcast_event("approval_required", {"filename": filename})

async def notify_social_posted(platform: str, url: str = None):
    await broadcast_event("social_posted", {"platform": platform, "url": url})
