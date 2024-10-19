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
                    "modality": ["text", "audio"],
                    "input_audio_format": "pcm16",
                    "input_audio_sample_rate": 24000,
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
                    print(res_1)
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
                        
                # Receive data from the WebSocket as bytes
                data = await ws.receive_bytes()

                # Convert received bytes to hex format
                # hex_data = data.hex()

                # Print the hexadecimal representation
                # logger.info(f"Received data (hex): {hex_data}")
                # logging.info("1")
                # You can also send this back to the client if needed
                # await ws.send_text(f"Received in hex: {hex_data}")




                break
            except WebSocketDisconnect:
                openai_connected = False
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error receiving data: {e}")
                break
            

            # logger.info('Session created')

            # while True:
            #     try:
            #         # Check if the client WebSocket is still open
            #         if ws.client_state == websockets.WebSocketState.DISCONNECTED:
            #             logger.info("Client WebSocket disconnected")
            #             return

            #         # Receive audio chunk from the client WebSocket
            #         audio_chunk = await asyncio.wait_for(ws.receive_bytes(), timeout=5.0)

            #         # Process the audio chunk
            #         event = audio_to_item_create_event(audio_chunk)
            #         if event is None:
            #             continue

            #         # Send audio chunk to OpenAI
            #         await openai_ws.send(event)

            #         # Receive and process the response from OpenAI
            #         openai_message = await asyncio.wait_for(openai_ws.recv(), timeout=10.0)
            #         openai_response = json.loads(openai_message)

            #         if openai_response['type'] == 'conversation.item.create.result':
            #             transcript = openai_response['item']['content'][0]['text']
            #             logger.info(f"Transcription: {transcript}")
                        
            #             # Send the transcription back to the client
            #             await ws.send_text(transcript)

            #     except asyncio.TimeoutError:
            #         logger.warning("Timeout while waiting for message")
            #     except websockets.exceptions.ConnectionClosed:
            #         logger.warning("OpenAI WebSocket connection closed")
            #         break
            #     except Exception as e:
            #         logger.error(f"Error processing message: {e}")
            #         if "disconnect message has been received" in str(e):
            #             logger.info("WebSocket disconnected")
            #             return

    except websockets.exceptions.ConnectionClosed:
        logger.error("OpenAI WebSocket connection closed")
        await asyncio.sleep(1)  # Wait before retrying
    except Exception as e:
        logger.error(f"Error in OpenAI connection: {e}")
        await asyncio.sleep(1)  # Wait before retrying

