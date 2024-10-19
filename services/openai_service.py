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

def audio_to_item_create_event(audio_bytes: bytes) -> str:
    try:
        # Load the audio file from the byte stream without specifying format
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
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return None

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
        
        # Setting a session
        await openai_ws.send(
            json.dumps({
                "type": "session.update",
                "session": {
                    "instructions": "You are a helpful assistant that transcribes audio to text.",
                    "modalities": ["text", "audio"],
                    "input_audio_format": "pcm16",
                    "input_audio_transcription": {
                        "model": "whisper-1"
                    },
                }
            })
        )
        
        logger.info(f"SESSION SETUP SUCCESSFULLY!")

        # Communication loop
        while True:
            try:

                async for response in openai_ws:
                    res_1=json.loads(response)
                    print('res1')
                    print(res_1)
                    if res_1["type"]=="session.updated":
                        text_message = {
                            'event_id':res_1['event_id'],
                            "type": "conversation.item.create",
                            "item": {
                                "type": "message",
                                "role": "user",
                                "content": [{"type": "input_text", "text":"what is 5+5"}]
                                }
                        }
                        
                        print('sending text message')
                        print(text_message)
                        print(json.dumps(text_message))
                        await openai_ws.send(json.dumps(text_message))
            
                        async for response in openai_ws:
                            res2=json.loads(response)
                            print('res2')
                            print(res2)
                            if res2['type'] == 'conversation.item.created':
                                message = {
                                'event_id': res2['event_id'],
                                "type": "response.create",
                                "response": {
                                "modalities": ["text"],
                                # "voice": "alloy",
                                "instructions": "Please assist the user",
                                # "output_audio_format": "pcm16"
                                }
                                }
                                await openai_ws.send(json.dumps(message))
                                async for response in openai_ws:
                                    result = json.loads(response)
                                    print('result', result)

                # Receive data from the WebSocket as bytes
                data = await ws.receive_bytes()

                # Convert received bytes to hex format
                # hex_data = data.hex()

                # Print the hexadecimal representation
                # logger.info(f"Received data (hex): {hex_data}")
                # logging.info("1")
                # You can also send this back to the client if needed
                # await ws.send_text(f"Received in hex: {hex_data}")




            except WebSocketDisconnect:
                openai_connected = False
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

