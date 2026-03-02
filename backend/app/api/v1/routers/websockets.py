from fastapi import APIRouter, WebSocket

from app.core.websocket import manager

router = APIRouter(tags=["websockets"])

@router.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str, token: str):
    # In reality, we will decode and validate the JWT token here
    # before calling manager.connect
    await manager.connect(user_id, websocket)
    try:
        while True:
            # Keep connection open, wait for client pings or msgs
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except Exception:
        manager.disconnect(user_id, websocket)
