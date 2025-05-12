import redis
from .models import Task
from .dependency_manager import update_dependent_tasks

r = redis.Redis()
def handle_task_status_update(task_id, status):
    task = Task.objects.get(pk=task_id)
    task.status = status
    task.save()
    if status == 'completed': update_dependent_tasks(task)