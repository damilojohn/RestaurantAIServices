from fastapi import FastAPI, WebSocket, WebSocketDisconnect, APIRouter
from typing import List
import json
import logging
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# WebSocket endpoints
router = APIRouter(
    prefix="",
    tags=["websocket", "AI Services"]
)

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Message received: {data}", websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def notify_new_predictions(predictions):
    """Notify dashboard of new predictions"""
    message = {
        "type": "new_predictions",
        "timestamp": datetime.now().isoformat(),
        "count": len(predictions),
        "predictions": predictions[:5]  # Send first 5 as preview
    }
    await manager.broadcast(json.dumps(message))
    logger.info(f"Broadcasted notification for {len(predictions)} predictions")