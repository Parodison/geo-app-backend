import json
from fastapi import WebSocket
from conf.settings import REDIS_INSTANCE
from datetime import datetime, date, timezone
from sqlmodel import Session, select
from conf.database import engine
from users.models import User
from geolocation.types import WebsocketConnectionInfo
from works.models import WorkMember
    
class GeolocationManager:
    active_connections: list[WebsocketConnectionInfo] = []
    
    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.redis = REDIS_INSTANCE
        
        self.available_operations = {
            "get_active_workers": self.get_active_workers,
            "update_location": self.update_location,
            "mark_arrival": self.mark_arrival,
        }
        
    async def validate_connection(self, user_id):
        await self.websocket.accept()
        
        self.active_connections.append({
            "user_id": user_id,
            "websocket": self.websocket,
            "connected_at": datetime.now(timezone.utc),
        })
        
        while True:
            data = await self.websocket.receive_json()
            await self.dispatch(data)
        
    async def dispatch(self, data: dict):
        requested_operation = data.get('operation')
        
        operation = self.available_operations.get(requested_operation)
        
        if not operation:
            invalid_operation = {
                "error": "Operación inválida",
                "operaciones_válidas": list(self.available_operations.keys())
            }
            await self.websocket.send_json(invalid_operation)
            return
        
        await operation(data)
                
    async def get_active_workers(self):
        
        search_workers = self.redis.scan_iter("user_location:*")
        
        active_workers = []
        
        for worker in search_workers:
            data = self.redis.get(worker)
            if data:
                active_workers.append(json.loads(data))
        
        await self.websocket.send_json(active_workers)
    
    async def update_location(self, data: dict):
        user_id = data.get('user_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        last_location = self.redis.get(f"user_location:{user_id}")
        
        if not last_location:
            with Session(bind=engine) as session:
                user = session.get(User, user_id)
                if not user:
                    await self.websocket.send_json({"error": "El usuario no existe"})
                    return
                
                first_name = user.first_name
                last_name = user.last_name
                
                self.redis.set(f"user_location:{user_id}", json.dumps({
                    "user_id": user_id,
                    "first_name": first_name,
                    "last_name": last_name,
                    "locations": [
                        {
                            "latitude": latitude,
                            "longitude": longitude,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    ]
                }))
                return
            
        else:
            user_location: dict = json.loads(last_location)
            locations: list = user_location.get('locations', [])
            locations.append({
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.redis.set(f"user_location:{user_id}", json.dumps(user_location))
            return
        
    async def mark_arrival(self, data: dict):
        user_id = data.get('user_id')
        work_id = data.get('work_id')
        
        if not user_id or not work_id:
            await self.websocket.send_json({"error": "Faltan los datos 'user_id' o 'work_id'"})
            return
        
        with Session(bind=engine) as session:
            work_member = session.get(WorkMember, (user_id, work_id))
            work_member.has_arrived = True
            work_member.arrive_time = datetime.now(timezone.utc)
            session.commit()
            
        await self.websocket.send_json({"message": "Se ha marcado la llegada con éxito"})
        return