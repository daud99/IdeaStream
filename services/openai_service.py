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

async def connect_to_openai_realtime(ws: WebSocket):
    """
    Establish a connection with the OpenAI real-time WebSocket API and
    manage communication between the client WebSocket and OpenAI WebSocket.
    
    Args:
        ws (WebSocket): The WebSocket connection from the client.
    """
    try:
        await ws.accept()
        WEBM_FILE_PATH = "/Users/daudahmed/Downloads/audio.webm"
        # Open the file in append-binary mode
        with open(WEBM_FILE_PATH, 'ab') as audio_file:
            while True:
                try:
                    # Receive data from the WebSocket as bytes
                    data = await ws.receive_bytes()
                    print(len(data))
                    # Write the received data to the WebM file
                    audio_file.write(data)

                except WebSocketDisconnect:
                    logger.info("Client disconnected")
                    break
                except Exception as e:
                    logger.error(f"Error receiving data: {e}")
                    break

    except websockets.exceptions.ConnectionClosed:
        logger.error("OpenAI WebSocket connection closed")
        await asyncio.sleep(1)  # Wait before retrying
    except Exception as e:
        logger.error(f"Error in OpenAI connection: {e}")
        await asyncio.sleep(1)  # Wait before retrying
