# models.py
from beanie import Document
from datetime import datetime
from pydantic import Field

class Transcript(Document):
    meeting_id: str
    text: str
    timestamp: datetime = Field(default_factory=datetime.now)

    class Settings:
        collection = "transcripts"

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_id": "12345",
                "text": "This is the meeting transcript...",
                "timestamp": "2024-10-18T10:00:00Z",
            }
        }
