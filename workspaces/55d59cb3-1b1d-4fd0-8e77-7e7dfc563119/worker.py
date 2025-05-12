from celery import Celery
import config

celery = Celery('tasks', broker=config.CELERY_CONFIG['CELERY_BROKER_URL'], backend=config.CELERY_CONFIG['CELERY_RESULT_BACKEND'])

@celery.task
def add(x, y, task_id):
    # Simulate task execution
    result = x + y
    return result
