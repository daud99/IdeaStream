from typing import List, Dict
from fastapi import WebSocket

# Dictionary to store WebSocket connections per meeting ID
meetings = {}  # Example structure: {meeting_id: [{"websocket": ws, "username": user_name}]}