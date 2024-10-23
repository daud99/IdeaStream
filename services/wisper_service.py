import json
import asyncio
import base64
import io
import os
import logging
import websockets
import pydub
import tempfile
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from openai import OpenAI
client = OpenAI()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_bytes_to_wavfile(wav_bytes):
    try:
        # Load WebM audio and convert to PCM16
        fname = "audio.wav"
        buffer = io.BytesIO(wav_bytes)
        buffer.name = fname
        audio = pydub.AudioSegment.from_file(buffer, format='wav')
        audio.export(buffer, format="wav")
        return buffer
    except Exception as e:
        logger.error(f"Error converting WebM to PCM: {e}")
        raise

def convert_to_mono_wav(input_path):
    try:
        # Load audio file with pydub
        audio = pydub.AudioSegment.from_file(input_path)
        
        # Convert to mono and 16kHz
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)  # 16-bit PCM
        
        # Save the converted file
        output_path = input_path.replace(".wav", "_converted.wav")
        audio.export(output_path, format="wav")
        
        return output_path
    except Exception as e:
        print(f"Error converting audio: {e}")
        return None

# Modify transcribe function to convert the file before sending to Whisper
def transcribe(audio_file_path):
    converted_file_path = convert_to_mono_wav(audio_file_path)
    if not converted_file_path:
        raise Exception("Error converting the audio file.")
    
    with open(converted_file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1", 
            file=audio_file
        )
    
    # Clean up converted file
    os.remove(converted_file_path)

    return transcription.text

# Real-time transcription using Whisper
async def realtime_transcription_using_whisper(ws: WebSocket):
    global client

    try:
        await ws.accept()   
        while True:
            try:
                # Receive audio data from the WebSocket as bytes
                data = await ws.receive_bytes()

                # Save the audio data to a temporary file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio_file:
                    temp_audio_file.write(data)
                    temp_audio_file.flush()
                    temp_audio_path = temp_audio_file.name

                # Send the file to Whisper API for transcription
                res = transcribe(temp_audio_path)

                # Send the transcription result back to the WebSocket client
                await ws.send_text(json.dumps(res))
                
                # Clean up the temporary file
                os.remove(temp_audio_path)
                                            
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error receiving data: {e}")
                break
    except websockets.exceptions.ConnectionClosed:
        logger.error("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in connection: {e}")

