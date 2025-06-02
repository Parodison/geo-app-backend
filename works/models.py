import sqlmodel
from fastapi import Request
from datetime import datetime, timedelta
from typing import Optional
from conf.exceptions import APIException
from users.models import User
from vehicles.models import Vehicle
from works import tasks

class WorkMember(sqlmodel.SQLModel, table=True):
    __tablename__ = "miembros_trabajo"
    id: Optional[int] = sqlmodel.Field(primary_key=True)
    user_id: int = sqlmodel.Field(foreign_key="usuarios.id")
    work_id: int = sqlmodel.Field(foreign_key="trabajos.id")
    role: Optional[str]
    has_arrived: Optional[bool] = sqlmodel.Field(default=False)
    arrive_time: Optional[datetime] = sqlmodel.Field(default=None)
    send_late_notification_task_id: Optional[str] = sqlmodel.Field(default=None)
    

class Work(sqlmodel.SQLModel, table=True):
    __tablename__ = "trabajos"
    id: Optional[int] = sqlmodel.Field(primary_key=True)
    latitude: float
    longitude: float
    location_name: str
    description: Optional[str] = sqlmodel.Field(default=None, sa_column=sqlmodel.Column(sqlmodel.Text))
    date_start: Optional[datetime]
    date_end: Optional[datetime]
    vehicle_id: Optional[int] = sqlmodel.Field(default=None, sa_column=sqlmodel.Column(sqlmodel.ForeignKey("vehiculos.id", ondelete="CASCADE")))
    driver_id : Optional[int] = sqlmodel.Field(default=None, sa_column=sqlmodel.Column(sqlmodel.ForeignKey("usuarios.id", ondelete="CASCADE")))
    status: str = sqlmodel.Field(default="pending")
    

    async def validate(self, request: Request, session: sqlmodel.Session):

        required_fields = [
            "latitude",
            "longitude",
            "location_name",
            "date_start",
            "date_end",
            "members",
        ]

        errors = []
        validated_fields = {}

        content_type = request.headers.get("content-type")

        if not content_type or not content_type.startswith("application/json"):
            raise APIException({"error": "Sólo se permiten formularios JSON"}, status_code=400)

        data: dict = await request.json()
        if "vehicle_id" in data:
            
            required_fields.append("driver_id")
            if not isinstance(data["vehicle_id"], int):
                raise APIException({"error": "El campo vehicle_id debe ser la primary key del vehículo"}, status_code=400)

            vehicle = session.get(Vehicle, data["vehicle_id"])
            
            if not vehicle:
                raise APIException({"error": "El vehículo no existe"}, status_code=400)
            driver = session.get(User, data["driver_id"])
            
            if not driver:
                raise APIException({"error": "No existe el usuario introducido"}, status_code=404)
        
        for field in required_fields:
            if field not in data:
                errors.append(f"El campo {field} es requerido")
                
        if not isinstance(data.get("members", []), list):
            errors.append("El campo members debe ser una lista de usuarios con sus roles del trabajo")
            
        else:
            members: list = data.get("members", [])
            
            for member in members:
                if not "user_id" or not "role" in member:
                    errors.append("El campo members debe ser una lista de usuarios con sus roles del trabajo")
                
                if not session.get(User, member["user_id"]):
                    
                    errors.append(f"El usuario con id: {member['user_id']} no existe")
                
                validated_fields["members"] = members           
        
        if errors:
            raise APIException({"error": errors}, status_code=400)

        for key, value in data.items():
            validated_fields[key] = value  

        validated_fields["date_start"] = datetime.strptime(validated_fields["date_start"], "%Y-%m-%dT%H:%M")
        validated_fields["date_end"] = datetime.strptime(validated_fields["date_end"], "%Y-%m-%dT%H:%M")
        
        return validated_fields

    async def save(self, data: dict, session: sqlmodel.Session):
        members: list[dict] = data.pop("members", [])
        for key, value in data.items():
            setattr(self, key, value)

        session.add(self)
        session.flush()
        
        for member_data in members:
            user_id = member_data.get("user_id")
            role = member_data.get("role")
                
            member = WorkMember(
                user_id=user_id,
                work_id=self.id,
                role=role,
            )
            
            start_late_arrival_notification = tasks.send_late_arrival_notification.apply_async(
                args=[user_id, self.id],
                eta=self.date_start + timedelta(minutes=15)
            )
            
            member.send_late_notification_task_id = start_late_arrival_notification.id
            print(f"Tarea programada con ID: {start_late_arrival_notification.id}")
            
            
            session.add(member)
        tasks.mark_work_as_active.apply_async(args=[self.id], eta=self.date_start)
        
        session.commit()
        session.refresh(self)