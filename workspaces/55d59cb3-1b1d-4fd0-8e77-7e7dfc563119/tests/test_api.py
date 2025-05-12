import pytest
import requests
import json
import time

BASE_URL = 'http://localhost:5000'

def test_create_task():
    task_data = {
        'task_type': 'test_task',
        'payload': {'data': 'test data'}
    }
    response = requests.post(f'{BASE_URL}/tasks', json=task_data)
    assert response.status_code == 201
    task_id = response.json()['task_id']
    return task_id

def test_get_task_result_pending():
    task_id = test_create_task()
    response = requests.get(f'{BASE_URL}/tasks/{task_id}')
    assert response.status_code == 202
    assert response.json()['status'] == 'PENDING'
    return task_id

def test_get_task_result_success():
    task_id = test_get_task_result_pending()
    time.sleep(5)  # Wait for the worker to complete the task
    response = requests.get(f'{BASE_URL}/tasks/{task_id}')
    assert response.status_code == 200
    assert 'Result of' in response.json()['result']

if __name__ == '__main__':
    pytest.main([__file__])
