import json
import uuid
import time
import os
import logging
import wave
import io
from fastapi import WebSocket, WebSocketDisconnect
from openai import OpenAI

client = OpenAI()

# Directory to save the audio recordings
SAVE_DIRECTORY = "recordings"
os.makedirs(SAVE_DIRECTORY, exist_ok=True)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

complete_transcription = None

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

def transcribe(audio_file_path):
    """Transcribe audio using Whisper API"""
    try:
        audio_file= open(audio_file_path, "rb")
        transcription = client.audio.translations.create(
            model="whisper-1", 
            file=audio_file
        )        
        return transcription.text
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None

import json

def perform_analysis(transcription):
    # Call OpenAI API for completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f'''
                You need to generate the titles and respective ideas based on the following transcription:
                \"\"\" 
                {transcription}
                \"\"\"
                The result should strictly be in the following JSON format without any extra explanation, text, or comments:
                {{
                  "titles": [
                    {{
                        "title": "Title 1",
                        "idea": "Idea 1",
                        "idea": "Idea 2"
                    }},
                    {{
                        "title": "Title 2",
                        "idea": "Idea 1",
                        "idea": "Idea 2"
                    }}
                  ],
                  "suggestions": [
                     "Suggestion 1"
                     "Suggestion 2"
                  ]
                }}
                Ensure the output is valid JSON and contains only the list structure provided.
                '''
            }
        ]
    )

    print('completion:')
    print(completion)
    # Access the content attribute correctly from the completion object
    response_text = completion.choices[0].message.content

    # Clean up the response text to extract valid JSON
    response_text = response_text.strip()  # Remove leading/trailing whitespace
    if response_text.startswith('```json') and response_text.endswith('```'):
        response_text = response_text[8:-3].strip()  # Remove the code block markers

    # Convert the response to a JSON object
    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError:
        response_json = {"error": "Invalid JSON format in response"}

    return response_json


async def realtime_transcription_using_whisper(ws: WebSocket):
    try:
        t = 0
        delta = 5
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
                    transcription = transcribe(saved_audio_path)
                    if transcription:
                        await ws.send_text( await ws.send_text(json.dumps({
                                    "status": "success",
                                    "type": "transcription",
                                    "text": transcription
                                })) )
                        logger.info(f"Transcription completed: {transcription}")
                        t+=1
                    # Remove the saved audio file after transcription
                    os.remove(saved_audio_path)
                    logger.info(f"Deleted audio file: {saved_audio_path}")
                else:
                    logger.error("Failed to save WAV file")
                    await ws.send_text(json.dumps({"error": "Failed to save audio file"}))
                    
                if t == delta:
                    output = perform_analysis(complete_transcription)
                    await ws.send_text( await ws.send_text(json.dumps({
                                    "status": "success",
                                    "type": "analysis",
                                    "text": output
                    })) )
                    delta += delta
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await ws.send_text(json.dumps({"error": str(e)}))
                
    except Exception as e:
        logger.error(f"Connection error: {e}")