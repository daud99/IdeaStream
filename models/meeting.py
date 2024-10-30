from beanie import Document, Link
from datetime import datetime
from typing import Optional, List
from pydantic import Field, ConfigDict
from bson import ObjectId
from enum import Enum
from models.user import User

class MeetingStatus(str, Enum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"

class Meeting(Document):
    title: Optional[str] = None
    description: Optional[str] = None
    date_time: datetime = Field(default_factory=datetime.now)
    duration: Optional[int] = None 
    status: MeetingStatus = Field(default=MeetingStatus.NEW)
    participants: list[str] = []  # Use forward declaration

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        populate_by_name=True,
        json_encoders={
            ObjectId: str
        }
    )

    class Settings:
        name = "Meeting"
        use_revision = True

    # Helper methods for participant management
    async def add_participant(self, user: User) -> bool:
        """Add a user to the meeting if they're not already participating."""
        if not await self.is_participant(user):
            self.participants.append(str(user.id))
            await self.save()
            return True
        return False

    async def remove_participant(self, user: User) -> bool:
        """Remove a user from the meeting if they're participating."""
        for participant in self.participants:
            if participant == str(user.id):
                self.participants.remove(participant)
                await self.save()
                return True
        return False

    async def get_participants(self) -> List[User]:
        """Fetch all participants with their full user details."""
        return [await participant.fetch() for participant in self.participants]

    async def is_participant(self, user: User) -> bool:
        """Check if a user is a participant in the meeting."""
        for participant in self.participants:
            if participant == str(user.id):
                return True
        return False