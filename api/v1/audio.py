from fastapi import APIRouter, WebSocket
from services.openai_service import process_audio_to_text

router = APIRouter()

@router.websocket("/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    while True:
        try:
            print('here')
            # Receive binary audio data
            audio_data = await websocket.receive_bytes()
            # Process audio data via OpenAI
            transcription = await process_audio_to_text(audio_data)

            # Send transcription back to the client
            await websocket.send_text(transcription)
        except Exception as e:
            await websocket.send_text(f"Error: {str(e)}")
