from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from models.meeting import Meeting, MeetingStatus
from models.user import User
from misc.utility import get_current_user
from typing import Dict, Any

router = APIRouter()

@router.post("/meeting/", response_model=Dict[str, Any])
async def create_meeting(meeting: Meeting, current_user: User = Depends(get_current_user)):
    """
    Create a new meeting and add the creator as the first participant.
    """
    try:
        # Set the creation timestamp and initialize the meeting status
        meeting.date_time = datetime.now()
        meeting.status = MeetingStatus.NEW
        
        # Initialize with empty participants list
        meeting.participants = []
        
        inserted_meeting = await meeting.insert()
        print("Inserted Meeting ID:", inserted_meeting.id)

        # Add the current user as a participant using proper Link initialization
        await meeting.add_participant(current_user)
        
        return {
            "meetingId": str(meeting.id),
            "name": current_user.first_name,
            "message": "Meeting created successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create meeting: {str(e)}"
        )

@router.post("/meeting/join/", response_model=Dict[str, str])
async def join_meeting(meeting_id: str, current_user: User = Depends(get_current_user)):
    """
    Allow a user to join an existing meeting, updating its status to IN_PROGRESS if necessary.
    """
    # Fetch the meeting by meeting_id
    meeting = await Meeting.get(meeting_id)
    if not meeting:
        raise HTTPException(status_code=404, detail="Meeting not found.")
    
    # Check and update the meeting status to IN_PROGRESS if it's not already
    if meeting.status == MeetingStatus.NEW:
        meeting.status = MeetingStatus.IN_PROGRESS
        await meeting.save()  # Save the updated status to the database
    
     # Check and update the meeting status to IN_PROGRESS if it's not already
    if meeting.status == MeetingStatus.FINISHED:
        raise HTTPException(status_code=404, detail="Meeting ALREADY finished.")

    # Check if user is already a participant
    if await meeting.is_participant(current_user):
        return {"message": f"User {current_user.first_name} is already in the meeting."}
    
    # Add the user to participants
    await meeting.add_participant(current_user)
    
    return {"message": f"User {current_user.first_name} has joined the meeting."}
