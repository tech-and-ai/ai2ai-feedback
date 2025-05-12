import pika
import json
import uuid
from src.config import RABBITMQ_HOST, RABBITMQ_QUEUE

class TaskScheduler:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    def schedule_task(self, task_definition, priority=1, dependencies=None):
        task_id = str(uuid.uuid4())
        task = {
            'task_id': task_id,
            'definition': task_definition,
            'priority': priority,
            'dependencies': dependencies or []
        }
        self.channel.basic_publish(
            exchange='',
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(task),
            properties=pika.BasicProperties(
                delivery_mode=2,  # make message persistent
            ))
        print(f"[x] Scheduled task: {task_id}")
        return task_id

    def close(self):
        self.connection.close()

if __name__ == '__main__':
    scheduler = TaskScheduler()
    task_def = {'command': 'echo Hello from task 1'}
    task_id = scheduler.schedule_task(task_def)
    print(f"Task ID: {task_id}")
    scheduler.close()
