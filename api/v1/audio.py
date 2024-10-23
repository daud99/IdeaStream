import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from jose import JWTError
from models.user import User
from misc.utility import decode_access_token
from services.realtime_service import connect_to_openai_realtime

router = APIRouter()

@router.websocket("/audio")
async def websocket_endpoint(websocket: WebSocket):
    # Accept the WebSocket connection
    await websocket.accept()
    
    # Get the token from the query parameters
    token = websocket.query_params.get("token")
    
    if token is None:
        await websocket.send_text("Authentication required: No token provided.")
        await websocket.close(code=1008)  # Policy Violation
        return

    # Validate the token and extract user information
    try:
        payload = decode_access_token(token)
        email: str = payload.get("sub")
        if email is None:
            await websocket.send_text(json.dumps({"msg": "Authentication required: An error occurred."}))
            await websocket.close(code=1008)  # Policy Violation
            return
        
        user = await User.find_one(User.email == email)
        if user is None:
            await websocket.send_text("Authentication required: User not found.")
            await websocket.close(code=1008)  # Policy Violation
            return
    except JWTError:
        await websocket.send_text("Authentication required: Token validation failed.")
        await websocket.close(code=1008)  # Policy Violation
        return
    except Exception as e:
        print(f"Error during authentication: {str(e)}")
        await websocket.send_text(json.dumps({"msg": "Authentication required: An error occurred."}))
        await websocket.close(code=1008)  # Policy Violation
        return

    # Proceed with your service logic
    try:
        await connect_to_openai_realtime(websocket)
        # Optionally handle real-time transcription
        # await realtime_transcription_using_whisper(websocket)
    except WebSocketDisconnect:
        print(f"Client {user.email} disconnected")
