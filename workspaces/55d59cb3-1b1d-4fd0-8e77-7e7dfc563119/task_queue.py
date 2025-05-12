import redis
import json
from config import REDIS_HOST, REDIS_PORT

class TaskQueue:
    def __init__(self, queue_name='task_queue', host=REDIS_HOST, port=REDIS_PORT):
        self.redis_client = redis.Redis(host=host, port=port, db=0)
        self.queue_name = queue_name

    def enqueue(self, task_data):
        self.redis_client.rpush(self.queue_name, json.dumps(task_data))

    def dequeue(self):
        _, task_data_json = self.redis_client.blpop(self.queue_name)
        return json.loads(task_data_json)

    def size(self):
        return self.redis_client.llen(self.queue_name)

if __name__ == '__main__':
    # Example usage
    task_queue = TaskQueue()
    task_data = {'task_id': 'test_task_1', 'task_type': 'example', 'payload': {'data': 'test data'}}
    task_queue.enqueue(task_data)
    print(f'Enqueued task: {task_data}')
    dequeued_task = task_queue.dequeue()
    print(f'Dequeued task: {dequeued_task}')
