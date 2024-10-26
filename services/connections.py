from typing import List, Dict
from fastapi import WebSocket

# List to store active WebSocket connections and their usernames
connected_clients: List[Dict[str, WebSocket]] = []
