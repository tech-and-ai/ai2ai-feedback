import graphviz as gv
from .models import Task

def visualize_dependencies():
    dot = gv.Digraph(comment='Task Dependencies')
    for task in Task.objects.all():
        dot.node(str(task.id), task.name)
        for dep in task.dependencies.all():
            dot.edge(str(dep.id), str(task.id))
    dot.render('tasks', format='png', view=True)
logger = logging.getLogger(__name__)