import numpy as np
import soundfile as sf
import base64
import asyncio
import websockets
import json
import logging
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


OPENAI_API_KEY=""
OPENAI_REALTIME_URL = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"

openai_ws = None
openai_connected = False

# Converts Float32 numpy array of audio data to PCM16
def float_to_16_bit_pcm(float32_array):
    # Clip values to the range [-1, 1] and scale to [-32768, 32767]
    int16_array = np.clip(float32_array, -1, 1) * 32767
    return int16_array.astype(np.int16)

# Converts a Float32 numpy array to base64-encoded PCM16 data
def base64_encode_audio(float32_array):
    pcm16_array = float_to_16_bit_pcm(float32_array)
    # Create a bytes representation of the PCM16 data
    pcm16_bytes = pcm16_array.tobytes()
    # Encode to base64
    return base64.b64encode(pcm16_bytes).decode('utf-8')

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

async def send_audio_over_websocket(audio_file_path):
    await connect_to_openai()
    # Read the audio file (only supports mono audio)
    audio_data, sample_rate = sf.read(audio_file_path)
    
    # Get channel data (only the first channel if stereo)
    if audio_data.ndim > 1:
        channel_data = audio_data[:, 0]  # Take only the first channel
    else:
        channel_data = audio_data

    # Encode the audio data
    base64_audio_data = base64_encode_audio(channel_data)

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

    # Establish WebSocket connection and send data
    await openai_ws.send(json.dumps(event))
    await openai_ws.send(json.dumps({"type": "response.create"}))
    async for response in openai_ws:
        res=json.loads(response)
        if res["type"] == "response.done":
            print('res')
            print(res)

# Example usage
if __name__ == "__main__":
    # Define the path to your audio file and WebSocket URL
    audio_file_path = '/Users/daudahmed/Downloads/harvard.wav'  # Path to your audio file
    
    # Run the function
    asyncio.run(send_audio_over_websocket(audio_file_path))
