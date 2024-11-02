import base64
import json
import uuid
import time
import os
import logging
import wave
import asyncio
from fastapi import WebSocket, WebSocketDisconnect
from openai import OpenAI
from services.fais import query_faiss_index, delete_faiss_index
from core.common import meetings  # Import shared `meetings` dictionary
from models.user import User
from models.meeting import Meeting, MeetingStatus

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
        channels = 1  # mono
        sample_width = 2  # 16-bit
        framerate = 16000  # 16kHz
        
        with wave.open(filepath, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(framerate)
            wav_file.writeframes(wav_bytes)
        
        return os.path.exists(filepath)
    except Exception as e:
        logger.error(f"Error saving WAV file: {e}")
        return False

def transcribe(audio_file_path):
    """Transcribe audio using Whisper API"""
    try:
        with open(audio_file_path, "rb") as audio_file:
            transcription = client.audio.translations.create(
                model="whisper-1", 
                file=audio_file
            )        
        return transcription.text
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        return None

async def perform_analysis(transcription):
    logger.info("BEGIN async analysis on the transcription")

    # Move blocking code to an async wrapper
    relevant_chunks = query_faiss_index(transcription)
    context = "\n".join(relevant_chunks)
    prompt = [
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f'''
                You need to generate titles and respective ideas, and categorize each idea based on the transcription below, with a slight influence from the context text. Prioritize the transcription content by approximately 60%, while using the context as a 40% reference. 

                Ensure that you use a maximum of five distinct categories for ideas. If new ideas do not fit into existing categories, consolidate them into the closest relevant category rather than creating a new one.

                You can create more than two suggestion at a time. Number of items in suggestions array can be ranging from 3-10.
                \"\"\"
                Transcription (Primary focus):
                {transcription}

                Context (Secondary reference):
                {context}
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
    

    # Call OpenAI API for completion
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=prompt
    )

    # Access the content attribute correctly from the completion object
    response_text = completion.choices[0].message.content.strip()

    # Clean up the response text to extract valid JSON
    if response_text.startswith('```json') and response_text.endswith('```'):
        response_text = response_text[8:-3].strip()  # Remove code block markers

    # Convert the response to JSON format
    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError:
        response_json = {"error": "Invalid JSON format in response"}

    return response_json

def generate_structured_summary(transcription):
    logger.info("BEGIN structured summary generation on the transcription")
    relevant_chunks = query_faiss_index(transcription)
    context = "\n".join(relevant_chunks)
    prompt = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": f'''
            Generate a structured and detailed summary for the following transcription, with additional context as a reference. Prioritize the transcription content by approximately 60%, using the context as a secondary influence at 40%. 

            \"\"\"
            Transcription (Primary focus):
            {transcription}

            Context (Secondary reference):
            {context}
            \"\"\"

            The result should be in the following JSON format without any additional comments, explanations, or extra text.
            The structure is defined, but each array should contain a variable number of items based on the meeting details, with a minimum of 5 items and a maximum of 20. Ensure that each array includes between 5 and 20 items as necessary, with detailed information, and make sure nothing is left empty.

            {{
                "key_outcomes": [],
                "decisions_made": [],
                "action_items": [],
                "overview": "A brief and descriptive overview of the main topics discussed during the meeting.",
                "important_takeaways": []
            }}
            '''
        }


    ]
    
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

    # Convert response to JSON for easier frontend display
    try:
        response_json = json.loads(response_text)
    except json.JSONDecodeError:
        response_json = {"error": "Invalid JSON format in response"}

    return response_json

async def realtime_transcription_using_whisper(ws: WebSocket, user: User, meetingId: str):
    try:
        complete_transcription = ''
        t = 0
        delta = 3
        while True:
            try:
                data = await ws.receive_text()
                message = json.loads(data)

                meeting_id = message.get("meetingId")
                type = message.get("type")
                audio_base64 = message.get("data")

                if type == "audio" and audio_base64:
                    try:
                        wav_data = base64.b64decode(audio_base64)
                    except base64.binascii.Error as e:
                        logger.error(f"Failed to decode base64 audio: {e}")
                        await ws.send_text(json.dumps({"error": "Invalid base64 audio data"}))
                        continue

                    filename = f"{uuid.uuid4()}_{int(time.time())}.wav"
                    saved_audio_path = os.path.join(SAVE_DIRECTORY, filename)

                    if save_wav_file(wav_data, saved_audio_path):
                        transcription = transcribe(saved_audio_path)
                        if transcription:
                            message = {
                                "status": "success",
                                "type": "transcription",
                                "text": transcription,
                                "user": f"{user.first_name} {user.last_name}"
                            }

                            for client in meetings.get(meeting_id, []):
                                await client["websocket"].send_text(json.dumps(message))

                            complete_transcription += transcription
                            t += 1

                        os.remove(saved_audio_path)
                    else:
                        await ws.send_text(json.dumps({"error": "Failed to save audio file"}))
                elif type == "end_meeting":
                    delete_faiss_index(os.path.join("indices", f"{meeting_id}.faiss"))
                    # Fetch the meeting by meeting_id and update its status
                    meeting = await Meeting.get(meeting_id)
                    if not meeting:
                        await ws.send_text(json.dumps({"error": "Failed to save audio file"}))
                    
                    # Update the meeting status to in_progress and add current user to participants
                    meeting.status = MeetingStatus.FINISHED
                    if not await meeting.is_participant(user):
                        meeting.add_participant(user)
                    await meeting.save()
                    # Send end meeting acknowledgment to all clients in the meeting
                    end_meeting_message = {
                        "status": "success",
                        "type": "end_meeting",
                        "message": "The meeting has been successfully ended."
                    }
                    for client in meetings.get(meeting_id, []):
                        await client["websocket"].send_text(json.dumps(end_meeting_message))
                    break
                elif type == "generate_summary":
                    output = generate_structured_summary(complete_transcription)
                    summary_message = {
                        "status": "success",
                        "type": "summary",
                        "output": output
                    }
                    for client in meetings.get(meeting_id, []):
                        await client["websocket"].send_text(json.dumps(summary_message))
                
                # Perform periodic analysis
                if t == delta:
                    output = perform_analysis(complete_transcription)
                    analysis_message = {
                        "status": "success",
                        "type": "analysis",
                        "output": output
                    }

                    for client in meetings.get(meeting_id, []):
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
