from typing import Literal
from fastapi import APIRouter, Depends, Request, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, Response
from sqlmodel import Session, select
from datetime import datetime
from conf.settings import REDIS_INSTANCE as r
from conf.database import get_db
from conf.exceptions import APIException
from works.models import Work, WorkMember

router = APIRouter()

@router.post("/create-work")
async def create_work(request: Request, db: Session = Depends(get_db)):
    try:
        work = Work()
        validated_data = await work.validate(request, db)
        await work.save(validated_data, db)
        
        return JSONResponse(
            content={"message": "Trabajo creado con éxito"},
            status_code=201
        )
        
    except APIException as e:
        return JSONResponse(content=e.response, status_code=e.status_code)

@router.get("/get-works")
async def get_works(
    db: Session = Depends(get_db),
    status: Literal["active", "inactive", "pending", "finished", "all"] = Query(...)
):
    works_list = []
    try:
        if status == "all":
            works = db.exec(select(Work).order_by(Work.date_start.desc())).all()

        else:
            works = list(db.exec(select(Work).where(Work.status == status).order_by(Work.date_start.desc())))
            
        if not works:
            return Response(status_code=204)
        
        for work in works:
            work_members = db.exec(select(WorkMember).where(WorkMember.work_id == work.id)).all()
            work_dump = work.model_dump()
            work_dump["members"] = len(work_members)

            works_list.append(jsonable_encoder(work_dump))
            
        return JSONResponse(content=works_list, status_code=200)
            
    except Exception as e:
        print(e)
        return JSONResponse(content={"mensaje": "Error al obtener las trabajos"}, status_code=500) 
            