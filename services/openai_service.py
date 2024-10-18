import json
import asyncio
import base64
import io
import websockets
from fastapi import WebSocket
from pydub import AudioSegment

from core.config import settings
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_REALTIME_URL = settings.OPENAI_REALTIME_URL

def audio_to_item_create_event(audio_bytes: bytes) -> str:
    # Load the audio file from the byte stream
    audio = AudioSegment.from_file(io.BytesIO(audio_bytes))
    
    # Resample to 24kHz mono pcm16
    pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2).raw_data
    
    # Encode to base64 string
    encoded_chunk = base64.b64encode(pcm_audio).decode()
    
    event = {
        "type": "conversation.item.create", 
        "item": {
            "type": "message",
            "role": "user",
            "content": [{
                "type": "input_audio", 
                "audio": encoded_chunk
            }]
        }
    }
    return json.dumps(event)

async def connect_to_openai_realtime(ws: WebSocket):
    """
    Establish a connection with the OpenAI real-time WebSocket API and
    manage communication between the client WebSocket and OpenAI WebSocket.
    
    Args:
        ws (WebSocket): The WebSocket connection from the client.
    """
    # Connect to OpenAI real-time WebSocket API
    async with websockets.connect(
        OPENAI_REALTIME_URL,
        extra_headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "OpenAI-Beta": "realtime=v1",
        },
    ) as openai_ws:
        
        # setting a session
        await openai_ws.send(
            json.dumps({
                "type": "session.update",
                "session": {
                    "instructions": "Your knowledge cutoff is 2023-10. You are a helpful assistant.",
                    "modality": "text",
                    "input_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                }
            })
        )

        try:
            # Create a task for receiving messages from OpenAI
            openai_receive_task = asyncio.create_task(openai_ws.recv())
            
            while True:
  
                # Receive audio chunk from the client WebSocket
                audio_chunk = await ws.receive_bytes()

                # Starting a conversation 
                await openai_ws.send(
                   audio_to_item_create_event(audio_chunk)
                )

                # Wait for the response from OpenAI
                done, pending = await asyncio.wait(
                    [openai_receive_task],
                    timeout=1.0,
                    return_when=asyncio.FIRST_COMPLETED
                )

                # If there is a response from OpenAI, process the transcribed text
                if openai_receive_task in done:
                    openai_message = await openai_receive_task
                    openai_response = json.loads(openai_message)

                    print(openai_response)

                    # Restart the OpenAI receive task
                    openai_receive_task = asyncio.create_task(openai_ws.recv())
        except Exception as e:
            print(f"Error in OpenAI connection: {e}")
        finally:
            await openai_ws.close()