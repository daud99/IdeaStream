from datetime import datetime
from fastapi import APIRouter
from models.meeting import Meeting

router = APIRouter()

# Endpoint to insert a new meeting
@router.post("/meeting/", response_model=str)
async def create_meeting(meeting: Meeting):

    meeting.date_time = datetime.now()
    meeting.duration = 60  

    await meeting.insert()
    return str(meeting.id)