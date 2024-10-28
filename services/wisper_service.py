import json
import uuid
import time
import os
import logging
import wave
from fastapi import WebSocket, WebSocketDisconnect
from openai import OpenAI
from services.common import connected_clients
from services.fais import query_faiss_index

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
        
        
        # Create a new WAV file with the parameters
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(framerate)
            wav_file.writeframes(wav_bytes)
        
        # Verify the file was created and is valid
        if os.path.exists(filepath): 
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

def perform_analysis(transcription):

    logger.info("BEGIN analysis on the transcription")
    # Retrieve relevant chunks using the transcription
    relevant_chunks = query_faiss_index(transcription)  # Assume this returns a list of relevant chunks
    

    # Combine the relevant chunks with the transcription for context
    context = "\n".join(relevant_chunks)  # Joining relevant chunks into a single string
    
    prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f'''
                You need to generate the titles and respective ideas, and also make sure to categorize each idea based on the following context and transcription:
                \"\"\"
                Context:
                {context}

                Transcription:
                {transcription}
                \"\"\"
                The result should strictly be in the following JSON format without any extra explanation, text, or comments:
                {{
                  "titles": [
                    {{
                        "title": "Title 1",
                        "ideas": ["Idea 1", "Idea 2"],
                        "category": "Category 1"
                    }},
                    {{
                        "title": "Title 2",
                        "ideas": ["Idea 1", "Idea 2"],
                        "category": "Category 2"
                    }}
                  ],
                  "suggestions": [
                     "Suggestion 1",
                     "Suggestion 2"
                  ]
                }}
                Ensure the output is valid JSON and contains only the list structure provided.
                '''
            }
        ]
    
    print('final prompt is as follow:')
    print(prompt)
    # Call OpenAI API for completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt
    )

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

async def realtime_transcription_using_whisper(ws: WebSocket, username: str):
    try:
        complete_transcription = ''
        t = 0
        delta = 3
        while True:
            try:
                data = await ws.receive_bytes()
                logger.info(f"Received audio data size: {len(data)} bytes")
                
                unique_filename = f"{uuid.uuid4()}_{int(time.time())}.wav"
                saved_audio_path = os.path.join(SAVE_DIRECTORY, unique_filename)
                
                if save_wav_file(data, saved_audio_path):
                    logger.info(f"Successfully saved WAV file: {saved_audio_path}")
                    
                    transcription = transcribe(saved_audio_path)
                    if transcription:
                        message = {
                            "status": "success",
                            "type": "transcription",
                            "text": transcription,
                            "user": username
                        }
                        
                        for client in connected_clients:
                            await client["websocket"].send_text(json.dumps(message))
                        
                        logger.info(f"Transcription completed: {transcription}")
                        complete_transcription += transcription
                        t += 1
                    
                    os.remove(saved_audio_path)
                    logger.info(f"Deleted audio file: {saved_audio_path}")
                else:
                    logger.error("Failed to save WAV file")
                    await ws.send_text(json.dumps({"error": "Failed to save audio file"}))
                    
                if t == delta:
                    output = perform_analysis(complete_transcription)
                    analysis_message = {
                        "status": "success",
                        "type": "analysis",
                        "output": output
                    }
                    
                    for client in connected_clients:
                        await client["websocket"].send_text(json.dumps(analysis_message))
                    
                    delta += delta
            except WebSocketDisconnect:
                logger.info("Client disconnected")
                break
            except Exception as e:
                logger.error(f"Error processing audio: {e}")
                await ws.send_text(json.dumps({"error": str(e)}))
                break
    except Exception as e:
        logger.error(f"Connection error: {e}")
        
