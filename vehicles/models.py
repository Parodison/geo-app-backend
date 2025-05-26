from datetime import datetime, timezone
import sqlmodel
from typing import Optional
from pathlib import Path
from conf.settings import MEDIA_DIR, env
from fastapi import Request, UploadFile
from conf.exceptions import APIException
from fastapi.encoders import jsonable_encoder

class Vehicle(sqlmodel.SQLModel, table=True):
    __tablename__ = "vehiculos"
    id: Optional[int] = sqlmodel.Field(primary_key=True)
    brand: str
    model: str
    year: int
    license_plate: str
    status: str = sqlmodel.Field(default="activo")
    registration_date: datetime = sqlmodel.Field(default_factory=lambda: datetime.now(timezone.utc))
    photo: Optional[str] = None

    def media_folder(self) -> Path:
        photo_folder = MEDIA_DIR / "vehicles"
        photo_folder.mkdir(parents=True, exist_ok=True)

        return photo_folder
    
    async def save_photo(self, photo: UploadFile) -> None:
        path = self.media_folder() / photo.filename
        with open(path, "wb") as buffer:
            buffer.write(await photo.read())
        
        return path.as_posix()

    async def validate(self, request: Request, session: sqlmodel.Session):
        content_type = request.headers.get("content-type")

        required_fields = [
            "brand",
            "model",
            "year",
            "license_plate",
        ]
        
        errors = []
        validated_fields = {}
        form = await request.form()

        if not content_type or not content_type.startswith("multipart/form-data"):
            raise APIException({"error": "Sólo se permiten formularios multipart/form-data"}, status_code=400)

        for field in required_fields:
            if field not in form:
                errors.append(f"El campo {field} es requerido")
        
        if errors:
            raise APIException({"error": errors}, status_code=400)
        
        for key, value in form.items():
            validated_fields.update({key: value})

        if request.method == "POST":
            existing_vehicle = session.exec(sqlmodel.select(Vehicle).where(Vehicle.license_plate == validated_fields["license_plate"])).first()
            if existing_vehicle:
                raise APIException({"error": f"El vehículo con matrícula '{validated_fields['license_plate']}' ya existe"}, status_code=400)

        return validated_fields
    
    async def save(self, data: dict, session: sqlmodel.Session):
        if 'photo' in data:
            photo_path = await self.save_photo(data['photo'])
            data["photo"] = photo_path

        for key, value in data.items():
            setattr(self, key, value)
        
        session.add(self)
        session.commit()
        session.refresh(self)

    async def update(self, request: Request, session: sqlmodel.Session):
        form = await request.form()
        
        data = {}
        
        for k, v in form.items():
            if k not in list(self.__fields__.keys()):
                raise APIException({"error": f"El campo {k} no es válido"}, status_code=400)
            data[k] = v
        
        if 'photo' in data:
            old_photo_path = Path(self.photo)
            if old_photo_path.exists():
                old_photo_path.unlink()

            new_photo_path = await self.save_photo(data['photo'])
            data["photo"] = new_photo_path
        
        for key, value in data.items():
            setattr(self, key, value)
        
        session.add(self)
        session.commit()
        session.refresh(self)
        
    @property
    def data(self):
        data = self.__dict__

        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.strftime("%d/%m/%Y")
            if key == "photo":
                data[key] = f"{env.base_url}{value}"
        
        
        return jsonable_encoder(data)
        

