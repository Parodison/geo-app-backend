from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from sqlmodel import Session
from datetime import datetime
from conf.settings import REDIS_INSTANCE as r
from conf.database import get_db
from conf.exceptions import APIException
from works.models import Work

router = APIRouter()

@router.post("/create-work")
async def create_work(request: Request, db: Session = Depends(get_db)):
    try:
        work = Work()
        validated_data = await work.validate(request, db)
        await work.save(validated_data, db)
        
        return JSONResponse(
            content={"mensaje": "Trabajo creado con éxito"},
            status_code=201
        )
        
    except APIException as e:
        return JSONResponse(content=e.response, status_code=e.status_code)
