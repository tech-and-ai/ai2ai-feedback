from .models import Task
import logging

def update_dependent_tasks(task):
    for dependent in task.dependencies.all():
        if all(dep.status == 'completed' for dep in Task.objects.filter(id=dependent.id)):
            dependent.status = 'ready'
            dependent.save()
            update_dependent_tasks(dependent)

logger = logging.getLogger(__name__)

def check_circular_dependency(task, visited):
    if task in visited: return True
    visited.add(task)
    for dep in task.dependencies.all():
        if check_circular_dependency(dep, visited): return True
    visited.remove(task)
    return False