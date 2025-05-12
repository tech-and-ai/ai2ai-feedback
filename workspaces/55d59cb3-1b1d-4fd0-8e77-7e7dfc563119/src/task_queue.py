import pika
import json
from src.config import RABBITMQ_HOST, RABBITMQ_QUEUE

class TaskQueue:
    def __init__(self):
        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        self.channel = self.connection.channel()
        self.channel.queue_declare(queue=RABBITMQ_QUEUE, durable=True)

    def enqueue_task(self, task_definition, priority=1, dependencies=None):
        task = {
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
        print(f"[x] Enqueued task: {task_definition}")

    def close(self):
        self.connection.close()

if __name__ == '__main__':
    queue = TaskQueue()
    queue.enqueue_task({'command': 'echo Hello from task queue'})