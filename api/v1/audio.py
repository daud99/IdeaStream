import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from jose import JWTError
from models.user import User
from misc.utility import decode_access_token
from services.realtime_service import connect_to_openai_realtime
from services.wisper_service import realtime_transcription_using_whisper
from services.common import meetings
# rest of your imports and code in AUDIO.py remain the same

router = APIRouter()

@router.websocket("/audio/{meeting_id}")
async def websocket_endpoint(websocket: WebSocket, meeting_id: str):
    await websocket.accept()

    # Authentication
    token = websocket.query_params.get("token")
    if token is None:
        await websocket.send_text("Authentication required: No token provided.")
        await websocket.close(code=1008)
        return

    try:
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            await websocket.send_text(json.dumps({"msg": "Authentication required: An error occurred."}))
            await websocket.close(code=1008)
            return
        
        user = await User.find_one(User.email == email)
        if user is None:
            await websocket.send_text("Authentication required: User not found.")
            await websocket.close(code=1008)
            return
    except JWTError:
        await websocket.send_text("Authentication required: Token validation failed.")
        await websocket.close(code=1008)
        return
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        await websocket.send_text(json.dumps({"msg": "Authentication required: An error occurred."}))
        await websocket.close(code=1008)
        return

    username = f"{user.first_name} {user.last_name}"

    # Add user to the specified meeting
    if meeting_id not in meetings:
        meetings[meeting_id] = []
    meetings[meeting_id].append({"websocket": websocket, "username": username})

    try:
        # Run transcription service for the user in the specific meeting
        await realtime_transcription_using_whisper(websocket, user, meeting_id)
    except WebSocketDisconnect:
        print(f"Client {user.email} disconnected from meeting {meeting_id}")
    finally:
        # Remove user from the meeting upon disconnection
        meetings[meeting_id].remove({"websocket": websocket, "username": username})
        if not meetings[meeting_id]:  # Remove empty meeting
            del meetings[meeting_id]
