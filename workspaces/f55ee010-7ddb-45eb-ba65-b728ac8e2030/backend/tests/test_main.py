
from fastapi.testclient import TestClient
from backend.main import app
from backend.models import TaskCreate
from datetime import date

client = TestClient(app)


def test_create_task():
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "due_date": str(date.today())
    }
    response = client.post("/tasks/", json=task_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["status"] == "pending"
    assert "id" in data


def test_read_tasks():
    # First create a task
    task_data = {
        "title": "Test Task 2",
        "description": "Test Description 2",
        "due_date": str(date.today())
    }
    create_response = client.post("/tasks/", json=task_data)
    assert create_response.status_code == 201

    response = client.get("/tasks/")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) > 0
    assert tasks[0]["title"] in ["Test Task", "Test Task 2"]


def test_update_task():
    # First create a task
    task_data = {
        "title": "Test Task 3",
        "description": "Test Description 3",
        "due_date": str(date.today())
    }
    create_response = client.post("/tasks/", json=task_data)
    assert create_response.status_code == 201
    task = create_response.json()
    task_id = task["id"]

    response = client.put(f"/tasks/{task_id}", json={"status": "completed"})
    assert response.status_code == 200
    updated_task = response.json()
    assert updated_task["status"] == "completed"


def test_delete_task():
    # First create a task
    task_data = {
        "title": "Test Task 4",
        "description": "Test Description 4",
        "due_date": str(date.today())
    }
    create_response = client.post("/tasks/", json=task_data)
    assert create_response.status_code == 201
    task = create_response.json()
    task_id = task["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    # Verify that the task is deleted
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404
