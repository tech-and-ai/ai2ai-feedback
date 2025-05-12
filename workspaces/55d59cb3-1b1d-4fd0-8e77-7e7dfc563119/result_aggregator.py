import redis
from config import REDIS_HOST, REDIS_PORT

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)

def get_result(task_id):
    result = redis_client.get(f'result:{task_id}')
    if result:
        return result.decode('utf-8')
    else:
        return None

if __name__ == '__main__':
    # Example usage
    task_id = 'test_task_1'
    result = get_result(task_id)
    if result:
        print(f'Result for task {task_id}: {result}')
    else:
        print(f'No result found for task {task_id}')
