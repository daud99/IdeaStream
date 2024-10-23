from fastapi import APIRouter, WebSocket
from services.realtime_service import connect_to_openai_realtime
from services.wisper_service import realtime_transcription_using_whisper

router = APIRouter()

@router.websocket("/audio")
async def websocket_endpoint(websocket: WebSocket):
    await connect_to_openai_realtime(websocket)
    # await realtime_transcription_using_whisper(websocket)