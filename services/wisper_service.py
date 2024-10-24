import json
import asyncio
import uuid
import time
import os
import logging
import wave
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydub import AudioSegment
from openai import OpenAI

client = OpenAI()

# Directory to save the audio recordings
SAVE_DIRECTORY = "recordings"
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_wav_file(wav_bytes, filepath):
    """Save WAV bytes to a file with proper WAV format"""
    try:
        # Default WAV parameters if header reading fails
        channels = 1  # mono
        sample_width = 2  # 16-bit
        framerate = 16000  # 16kHz
        
        # First try to read the WAV header
        try:
            with io.BytesIO(wav_bytes) as wav_buffer:
                with wave.open(wav_buffer, 'rb') as wav_read:
                    channels = wav_read.getnchannels()
                    sample_width = wav_read.getsampwidth()
                    framerate = wav_read.getframerate()
                    frames = wav_read.readframes(wav_read.getnframes())
        except Exception as e:
            logger.warning(f"Could not read WAV header, using default values: {e}")
            # If we can't read the header, assume the bytes are raw PCM data
            frames = wav_bytes[44:]  # Skip the 44-byte WAV header
        
        # Create a new WAV file with the parameters
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(framerate)
            wav_file.writeframes(frames if isinstance(frames, bytes) else wav_bytes[44:])
        
        # Verify the file was created and is valid
        if os.path.exists(filepath) and os.path.getsize(filepath) > 44:  # 44 is minimum WAV header size
            return True
            
        return False
    except Exception as e:
        logger.error(f"Error saving WAV file: {e}")
        return False

def convert_to_whisper_format(input_path):
    """Convert audio to format compatible with Whisper API"""
    try:
        # Load the audio file
        audio = AudioSegment.from_wav(input_path)
        
        # Convert to required format: mono, 16kHz, 16-bit PCM
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        output_path = input_path.replace(".wav", "_whisper.wav")
        audio.export(output_path, format="wav")
        
        # Verify the converted file
        if os.path.exists(output_path) and os.path.getsize(output_path) > 44:
            return output_path
            
        return None
    except Exception as e:
        logger.error(f"Error converting audio: {e}")
        return None

def transcribe(audio_file_path):
    """Transcribe audio using Whisper API"""
    try:
        # Convert audio to Whisper-compatible format
        converted_file_path = convert_to_whisper_format(audio_file_path)
        if not converted_file_path:
            raise Exception("Error converting the audio file.")
        
        # Transcribe using Whisper API
        with open(converted_file_path, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
            )
        
        # Clean up converted file
        os.remove(converted_file_path)
        
        return transcription.text
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None

async def realtime_transcription_using_whisper(ws: WebSocket):
    try:
        while True:
            try:
                # Receive audio data
                data = await ws.receive_bytes()
                
                # Log the size of received data
                logger.info(f"Received audio data size: {len(data)} bytes")
                
                # Generate unique filename
                unique_filename = f"{uuid.uuid4()}_{int(time.time())}.wav"
                saved_audio_path = os.path.join(SAVE_DIRECTORY, unique_filename)
                
                # Save the WAV file
                if save_wav_file(data, saved_audio_path):
                    logger.info(f"Successfully saved WAV file: {saved_audio_path}")
                    
                    # Transcribe the audio
                    # transcription = transcribe(saved_audio_path)
                    # if transcription:
                    #     await ws.send_text(json.dumps({"transcription": transcription}))
                    #     logger.info(f"Transcription completed: {transcription}")
                    
                    # Optionally remove the original file if you don't want to keep it
                    # os.remove(saved_audio_path)
                else:
                    logger.error("Failed to save WAV file")
                    await ws.send_text(json.dumps({"error": "Failed to save audio file"}))
                    
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await ws.send_text(json.dumps({"error": str(e)}))
                
    except Exception as e:
        logger.error(f"Connection error: {e}")