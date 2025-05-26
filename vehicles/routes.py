from fastapi import (
    APIRouter, Depends, Request
)
from sqlmodel import Session, select
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from vehicles.models import Vehicle
from conf.database import get_db
from conf.exceptions import APIException
from conf.settings import env
from datetime import datetime

router = APIRouter()

@router.post("/create-vehicle")
async def create_vehicle(request: Request, db: Session = Depends(get_db)):
    try:

        vehicle = Vehicle()
        validated_data = await vehicle.validate(request, db)
        await vehicle.save(validated_data, db)

        return JSONResponse(content=vehicle.data, status_code=200)
    
    except APIException as e:
        return JSONResponse(content=e.response, status_code=e.status_code)
    
@router.get("/list-vehicles")
async def list_vehicles(db: Session = Depends(get_db)):
    vehicles_list = []

    vehicles = db.exec(select(Vehicle)).all()
    
    for vehicle in vehicles:
        vehicle = vehicle.model_dump()
        for key, value in vehicle.items():
            if isinstance(value, datetime):
                vehicle[key] = value.strftime("%d/%m/%Y")
            if key == "photo":
                vehicle[key] = f"{env.base_url}{value}"
        vehicles_list.append(vehicle)
        
    return JSONResponse(content=jsonable_encoder(vehicles_list), status_code=200)

@router.put("/update-vehicle/{vehicle_id}")
async def update_vehicle(vehicle_id: int, request: Request, db: Session = Depends(get_db)):
    try:
        vehicle = db.get(Vehicle, vehicle_id)
        if not vehicle:
            raise APIException({"error": "Vehicle not found"}, status_code=404)
        
        await vehicle.update(request, db)
        
        return JSONResponse(content=vehicle.data, status_code=200)
    except APIException as e:
        return JSONResponse(content=e.response, status_code=e.status_code)