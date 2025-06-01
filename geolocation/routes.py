from fastapi import APIRouter, WebSocket
from geolocation.geo_manager import GeolocationManager

router = APIRouter()

@router.websocket("/geolocations")
async def geolocation(websocket: WebSocket):
    geo_manager = GeolocationManager(websocket)
    await geo_manager.validate_connection()