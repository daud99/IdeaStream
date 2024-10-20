import json
import asyncio
import base64
import io
import logging
import websockets
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydub import AudioSegment

from core.config import settings
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_REALTIME_URL = settings.OPENAI_REALTIME_URL

openai_ws = None
openai_connected = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to convert webm to PCM16 bytes using pydub
def convert_webm_to_pcm_bytes(webm_file_path):
    # Load the webm file
    audio = pydub.AudioSegment.from_file(webm_file_path, format='webm')

    # Resample to 24kHz mono PCM16
    pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)

    # Return raw audio data
    return pcm_audio.raw_data

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

async def connect_to_openai_realtime(ws: WebSocket):
    """
    Establish a connection with the OpenAI real-time WebSocket API and
    manage communication between the client WebSocket and OpenAI WebSocket.
    
    Args:
        ws (WebSocket): The WebSocket connection from the client.
    """
    global openai_ws, openai_connected
    try:
        await ws.accept()

        # Ensure a connection to OpenAI is established only once
        await connect_to_openai()    

        if not openai_connected:
            await ws.send_text("Error: Could not connect to OpenAI WebSocket")
            await ws.close()
            return
        
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

        while True:
            try:
                # Receive audio data from the client
                audio_data = await ws.receive_bytes()
                if audio_data == b"":
                    break

                # Send audio data to OpenAI
                await openai_ws.send(audio_data)

                # Receive transcription from OpenAI
                response = await openai_ws.recv()
                await ws.send_text(response)
            except WebSocketDisconnect:
                break

       
               

    except websockets.exceptions.ConnectionClosed:
        logger.error("OpenAI WebSocket connection closed")
        await asyncio.sleep(1)  # Wait before retrying
    except Exception as e:
        logger.error(f"Error in OpenAI connection: {e}")
        await asyncio.sleep(1)  # Wait before retrying

