import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from src.api.websocket_manager import manager

logger = logging.getLogger("websocket")
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep alive and handle incoming if needed
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
