import openai
import io
from core.config import settings

openai.api_key = settings.OPENAI_API_KEY

async def process_audio_to_text(audio_data: bytes) -> str:
    audio_file = io.BytesIO(audio_data)

    try:
        response = openai.Audio.transcribe("whisper-1", audio_file)
        return response["text"]
    except Exception as e:
        return f"Error: {str(e)}"
