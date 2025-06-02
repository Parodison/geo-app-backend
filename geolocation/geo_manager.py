import json
import asyncio
from fastapi import WebSocket
from conf.settings import REDIS_INSTANCE
from datetime import datetime, date, timezone
from sqlmodel import Session, select
from conf.database import engine
from users.models import User
from geolocation.types import WebsocketConnectionInfo
from works.models import WorkMember
from conf.authentication import auth
from starlette.websockets import WebSocketDisconnect


active_connections: list[WebsocketConnectionInfo] = []
    
class GeolocationManager:
        
    def __init__(self, websocket: WebSocket = None):
        self.websocket = websocket
        self.redis = REDIS_INSTANCE
        
        self.available_operations = {
            "get_active_workers": self.get_active_workers,
            "update_location": self.update_location,
            "mark_arrival": self.mark_arrival,
        }

        self.users_locations_channel = "user_locations"

    async def locations_listener(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.users_locations_channel)

        while True:
            message = pubsub.get_message()
            if message and message["type"] == 'message':
                data = json.loads(message["data"])
                for connection in active_connections:
                    if connection["user_id"] != data["user_id"]:
                        await connection["websocket"].send_json(data)
                
            await asyncio.sleep(0.5)
        
        
    async def validate_connection(self):
        access_token = self.websocket.query_params.get("access_token")
        if not access_token:
            await self.websocket.close(code=1008, reason="No se proporcionó el access token")
            return
            
        access_token_data = auth.verify_access_token(access_token)
        
        if not access_token_data:
            await self.websocket.close(code=1008, reason="Access token inválido")
            return
            
        user_id = access_token_data["user_id"]
        
        for connection in active_connections:
            if connection["user_id"] == user_id:
                await connection["websocket"].close(code=4001, reason="Se ha iniciado sesión en otro dispositivo")
                active_connections.remove(connection)
        
        await self.websocket.accept()
        
        active_connections.append({
            "user_id": user_id,
            "websocket": self.websocket,
            "connected_at": datetime.now(timezone.utc),
        })


        try:
            while True:
                data = await self.websocket.receive_json()
                data["user_id"] = user_id
                await self.dispatch(data)
        except WebSocketDisconnect:
            for connection in active_connections:
                
                if connection["websocket"] == self.websocket:
                    active_connections.remove(connection)
        
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
                
    async def get_active_workers(self, data):
        
        search_workers = self.redis.scan_iter("user_location:*")
        
        active_workers = []
        
        for worker in search_workers:
            
            data = self.redis.get(worker)
            if data:
                active_workers.append(json.loads(data))
        
        await self.websocket.send_json(active_workers)
        return
    
    async def update_location(self, data: dict):
        user_id = data.get('user_id')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        last_location = self.redis.get(f"user_location:{user_id}")
        
        if not last_location:
            with Session(bind=engine) as session:
                print(f"Creando instancia de coordenadas para el usuario: {user_id}")
                user = session.get(User, user_id)
                if not user:
                    await self.websocket.send_json({"error": "El usuario no existe"})
                    return
                
                first_name = user.first_name
                last_name = user.last_name

                new_location = {
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
                }
                
                self.redis.set(f"user_location:{user_id}", json.dumps(new_location))
                self.redis.publish(self.users_locations_channel, json.dumps(new_location))
                return
            
        else:
            print(f"Actualizando instancia de coordenadas")
            user_location: dict = json.loads(last_location)
            locations: list = user_location.get('locations', [])

            new_location = {
                "latitude": latitude,
                "longitude": longitude,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            locations.append(new_location)
            
            self.redis.set(f"user_location:{user_id}", json.dumps(user_location))
            data_for_channel = {
                **user_location,
                "locations": new_location
            }
            
            self.redis.publish(self.users_locations_channel, json.dumps(data_for_channel))
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
