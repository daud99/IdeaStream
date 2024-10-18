from fastapi import APIRouter, WebSocket
from services.openai_service import connect_to_openai_realtime

router = APIRouter()

@router.websocket("/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    await connect_to_openai_realtime(websocket)
