from conf.settings import celery_app

@celery_app.task(name = "send_late_arrival_notification")
def send_late_arrival_notification(user_id, work_id):
    print(f"Se ha programado la tarea a los 15 minutos para el work id {work_id}")