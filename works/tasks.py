from conf.settings import celery_app
from celery.app.task import Task
from conf.database import engine
from sqlmodel import Session
from works.models import Work

@celery_app.task(name ="send_late_arrival_notification")
def send_late_arrival_notification(user_id, work_id):
    print(f"Ya pasaron más de 15 minutos de la hora de entrada y el usuario {user_id} no llegó a trabajar")
    
@celery_app.task(name="mark_work_as_active")    
def mark_work_as_active(work_id):
    with Session(engine) as session:
        work = session.get(Work, work_id)
        work.status = "active"
        session.commit()