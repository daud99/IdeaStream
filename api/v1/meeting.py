from datetime import datetime
from fastapi import APIRouter
from models.meeting import Meeting
from models.user import User
from misc.utility import get_current_user
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

router = APIRouter()

# Endpoint to insert a new meeting
@router.post("/meeting/", response_model=str)
async def create_meeting(meeting: Meeting, current_user: User = Depends(get_current_user)):

    meeting.date_time = datetime.now()
    meeting.duration = 60  

    await meeting.insert()
    return JSONResponse(content={
        "meetingId": str(meeting.id), 
        "name": current_user.first_name
    })
    # return f"Hello, {current_user.first_name} with {meeting.id}!"