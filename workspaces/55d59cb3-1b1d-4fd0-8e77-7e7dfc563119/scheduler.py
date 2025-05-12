import redis
import json
from config import REDIS_HOST, REDIS_PORT

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
TASK_QUEUE = 'task_queue'

def schedule_task(task_data):
    redis_client.rpush(TASK_QUEUE, json.dumps(task_data))
    print(f'Task {task_data["task_id"]} scheduled.')

if __name__ == '__main__':
    # Example usage (for testing purposes)
    task_data = {
        'task_id': 'test_task_1',
        'task_type': 'example_task',
        'payload': {'data': 'some data'}
    }
    schedule_task(task_data)
