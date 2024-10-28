import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from jose import JWTError
from models.user import User
from misc.utility import decode_access_token
from services.realtime_service import connect_to_openai_realtime
from services.wisper_service import realtime_transcription_using_whisper
from services.common import connected_clients
# rest of your imports and code in AUDIO.py remain the same

router = APIRouter()

@router.websocket("/audio")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
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
    connected_clients.append({"websocket": websocket, "username": username})

    try:
        await realtime_transcription_using_whisper(websocket, username)
    except WebSocketDisconnect:
        print(f"Client {user.email} disconnected")
    finally:
        connected_clients.remove({"websocket": websocket, "username": username})
