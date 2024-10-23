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

prompts = 0
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


def extract_transcript(response):
    try:
        # Navigate to the 'content' field where the text or audio transcript is stored
        content_list = response['response']['output'][0]['content']
        for content in content_list:
            # Check for text content with the phrase 'The transcript of the audio is:'
            if 'type' in content:
                if content['type'] == 'audio':
                    if 'transcript' in content:
                        if 'unable to process audio' in content['transcript'] or "How can I assist you" in content['transcript']:
                            return ''
                        elif ':' in content['transcript']:
                            transcript = content['transcript'].split(':')[1].strip().strip('"')
                            return transcript
                        else:
                            return content['transcript']
                elif content['type'] == 'text':
                    if 'text' in content:
                         if 'unable to process audio' in content['text']or "How can I assist you" in content['text']:
                            return ''
                         elif ':' in content['text']:
                            transcript = content['text'].split(':')[1].strip().strip('"')
                            return transcript
                         else:
                            return content['text']
        return ''
    except KeyError:
        return ''

def extract_titles(response):
    try:
        # Navigate to the 'content' field where the text is stored
        content_list = response['response']['output'][0]['content']
        for content in content_list:
            if 'text' in content:
                text = content['text']
                
                # Check if there's a colon to split by
                if ':' in text:
                    # Split by the colon, get the part after the colon
                    _, titles_part = text.split(':', 1)
                else:
                    # If no colon, use the whole text
                    titles_part = text
                
                # Split the titles part by newline and filter out any empty strings
                titles = [title.strip() for title in titles_part.split('\n') if title.strip()]
                return titles
        return []
    except KeyError:
        return []

async def generate_idea():
    global openai_ws, openai_connected, prompts
    await openai_ws.send(json.dumps(
        {
            "type": "response.create",
            "response": {
                "instructions": "This response is to have an analysis of the transcription so far? What do you think are main TITLES you can derive from discussion in conversation so far the one you have transcripted (converted) from audio to text, you can return those ideas seperated by new line (/n) Make sure title are not more than 5?"
            }
        }
    ))
    async for response in openai_ws:
        res = json.loads(response)
        if res["type"] == "response.done" and res["response"]["status"] != "failed":
            print(res)
            titles = extract_titles(res)
            break

    return titles


async def connect_to_openai_realtime(ws: WebSocket):
    """
    Establish a connection with the OpenAI real-time WebSocket API and
    manage communication between the client WebSocket and OpenAI WebSocket.
    
    Args:
        ws (WebSocket): The WebSocket connection from the client.
    """
    global openai_ws, openai_connected, prompts
    prompt_no = 3
    prompt_delta = 2
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
        
        
        while True:
                try:
                    # Receive audio data from the WebSocket as bytes
                    data = await ws.receive_bytes()

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
                    await openai_ws.send(json.dumps(
                        {
                            "type": "response.create",
                            "response": {
                                "instructions": "please transcript the audio"
                            }
                        }
                    ))

                    async for response in openai_ws:
                        res = json.loads(response)
                        if res["type"] == "response.done":
                            print('Response received from OpenAI:', res)
                            text = extract_transcript(res)
                            if text != '':
                                await ws.send_text(json.dumps({
                                    "status": "success",
                                    "type": "transcription",
                                    "text": text
                                })) 
                                prompts += 1 
                            break
                    
                    if prompts == prompt_no:
                        titles = await generate_idea()
                        if len(titles) != 0:
                            await ws.send_text(json.dumps({
                                "status": "success",
                                "type": "titles",
                                "titles": titles
                            })) 
                        prompts += prompt_delta
                    
                        
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

