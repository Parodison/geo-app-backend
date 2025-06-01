from typing import TypedDict
from fastapi import WebSocket
from datetime import datetime

class WebsocketConnectionInfo(TypedDict):
    user_id: int
    websocket: WebSocket
    connected_at: datetime