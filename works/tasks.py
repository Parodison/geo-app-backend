from conf.settings import celery_app
from celery.app.task import Task




@celery_app.task(name ="send_late_arrival_notification")
def send_late_arrival_notification(user_id, work_id):
    print(f"Ya pasaron más de 15 minutos de la hora de entrada y el usuario {user_id} no llegó a trabajar")
    