import asyncio
import json
import base64
import numpy as np
import pydub
import websockets
import logging
import subprocess
import io
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


OPENAI_API_KEY=""
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

openai_ws = None
openai_connected = False

# Connect to OpenAI WebSocket
async def connect_to_openai():
    global openai_ws, openai_connected
    if not openai_connected:
        try:
            openai_ws = await websockets.connect(
                OPENAI_REALTIME_URL,
                extra_headers={
                    "Authorization": f"Bearer {OPENAI_API_KEY}",
                    "OpenAI-Beta": "realtime=v1",
                },
            )
            openai_connected = True
            logger.info("Connected to OpenAI WebSocket")
        except websockets.exceptions.ConnectionClosed as e:
            logger.error("OpenAI WebSocket connection closed: %s", e)
            openai_connected = False
        except Exception as e:
            logger.error("Error in OpenAI connection: %s", e)
            openai_connected = False

# Function to convert webm to PCM16 bytes using pydub
def convert_webm_to_pcm_bytes(webm_file_path):
    # Load the webm file
    audio = pydub.AudioSegment.from_file(webm_file_path, format='webm')

    # Resample to 24kHz mono PCM16
    pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)

    # Return raw audio data
    return pcm_audio.raw_data

# Function to send audio over WebSocket
async def send_audio_over_websocket(audio_file_path):
    await connect_to_openai()

    # Convert webm to PCM16 bytes
    pcm_bytes = convert_webm_to_pcm_bytes(audio_file_path)

    # Encode PCM bytes to base64
    base64_audio_data = base64.b64encode(pcm_bytes).decode('utf-8')

    await openai_ws.send(
        json.dumps({
            "type": "session.update",
            "session": {
                "modalities": ["text"],
                "instructions": "You are a helpful assistant that transcribes audio to text.",
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                }
            }
        })
    )

    # Create the event structure
    event = {
        "type": "conversation.item.create",
        "item": {
            "type": "message",
            "role": "user",
            "content": [
                {
                    "type": "input_audio",
                    "audio": base64_audio_data
                }
            ]
        }
    }

    # Send data over WebSocket
    await openai_ws.send(json.dumps(event))
    await openai_ws.send(json.dumps({"type": "response.create"}))
    async for response in openai_ws:
        res = json.loads(response)
        if res["type"] == "response.done":
            print('res')
            print(res)
            
# Example usage
if __name__ == "__main__":
    # Define the path to your audio file and WebSocket URL
    audio_file_path = '/Users/daudahmed/Downloads/audio.webm'  # Path to your audio file
    
    # Run the function
    asyncio.run(send_audio_over_websocket(audio_file_path))
