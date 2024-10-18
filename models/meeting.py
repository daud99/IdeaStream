from beanie import Document
from datetime import datetime
from typing import Optional
from pydantic import Field

class Meeting(Document):
    title: Optional[str] = None
    description: Optional[str] = None
    date_time: datetime = Field(default_factory=datetime.now)
    duration: Optional[int] = None 

    class Settings:
        collection = "meetings"

    class Config:
        schema_extra = {
            "example": {
                "title": "Project Kickoff",
                "description": "Initial meeting to discuss the project requirements.",
                "duration": 60  # date_time is not included in the example
            }
        }