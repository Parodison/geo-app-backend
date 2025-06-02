from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
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
async def get_works(db: Session = Depends(get_db)):
    works_list = []
    try:
        works = db.exec(select(Work).order_by(Work.date_start.desc())).all()
        for work in works:
            work_dump = work.model_dump()
            
            work_members = db.exec(select(WorkMember).where(WorkMember.work_id == work.id)).all()
            
            work_dump["members"] = [member.model_dump() for member in work_members]
            works_list.append(work_dump)
            
        return JSONResponse(content=works_list, status_code=200)
            
    except Exception as e:
        print(e)
        return JSONResponse(content={"mensaje": "Error al obtener las trabajos"}, status_code=500) 
            