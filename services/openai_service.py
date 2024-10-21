import json
import asyncio
import base64
import io
import logging
import websockets
import pydub
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from core.config import settings
OPENAI_API_KEY = settings.OPENAI_API_KEY
OPENAI_REALTIME_URL = settings.OPENAI_REALTIME_URL

openai_ws = None
openai_connected = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to handle conversion from webm to PCM
def convert_webm_to_pcm_bytes(webm_bytes):
    try:
        # Load WebM audio and convert to PCM16
        audio = pydub.AudioSegment.from_file(io.BytesIO(webm_bytes), format='webm')
        pcm_audio = audio.set_frame_rate(24000).set_channels(1).set_sample_width(2)
        return pcm_audio.raw_data
    except Exception as e:
        logger.error(f"Error converting WebM to PCM: {e}")
        raise

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
        # Ensure a connection to OpenAI is established only once
        await connect_to_openai()    

        if not openai_connected:
            await ws.send_text("Error: Could not connect to OpenAI WebSocket")
            await ws.close()
            return
        
        # Send session initialization request to OpenAI
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
        await ws.accept()
        
        # Create an audio file path for saving received data (optional for debugging)
        WEBM_FILE_PATH = "/Users/umarmukhtar/Downloads/audio.webm"
        
        with open(WEBM_FILE_PATH, 'ab') as audio_file:
            while True:
                try:
                    # Receive audio data from the WebSocket as bytes
                    data = await ws.receive_bytes()
                    audio_file.write(data)  # Optional: Save received audio

                    # Encode PCM bytes to base64
                    base64_audio_data = base64.b64encode(data).decode('utf-8')

                    # Create event to send to OpenAI
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

                    await openai_ws.send(json.dumps(event))
                    await openai_ws.send(json.dumps({"type": "response.create"}))

                    async for response in openai_ws:
                        res = json.loads(response)
                        if res["type"] == "response.done":
                            print('Response received from OpenAI:', res)
                            await ws.send_text(json.dumps(res))
                                
                            break
                        
                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error receiving data: {e}")
                    break

    except websockets.exceptions.ConnectionClosed:
        logger.error("OpenAI WebSocket connection closed")
        await asyncio.sleep(1)
    except Exception as e:
        logger.error(f"Error in OpenAI connection: {e}")
        await asyncio.sleep(1) 

