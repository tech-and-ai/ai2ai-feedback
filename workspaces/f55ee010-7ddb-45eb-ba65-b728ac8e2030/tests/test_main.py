
from fastapi.testclient import TestClient
from backend.main import app, get_db, Base, engine
from backend.models import TaskStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from datetime import date

# Setup a test database
TEST_DATABASE_URL = "sqlite:///./test.db"

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture()
def client(test_db):
    def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)
    yield client
    app.dependency_overrides = {}


def test_create_task(client):
    response = client.post(
        "/tasks",
        json={"title": "Test Task", "description": "Test Description", "due_date": "2024-01-01", "status": "pending"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["description"] == "Test Description"
    assert data["due_date"] == "2024-01-01"
    assert data["status"] == "pending"
    assert "id" in data


def test_read_tasks(client):
    # First, create a task
    client.post(
        "/tasks",
        json={"title": "Test Task 2", "description": "Test Description 2", "due_date": "2024-01-02", "status": "in_progress"},
    )

    response = client.get("/tasks")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["title"] == "Test Task 2" # Assuming this is the first task


def test_read_task(client):
    # First, create a task
    create_response = client.post(
        "/tasks",
        json={"title": "Test Task 3", "description": "Test Description 3", "due_date": "2024-01-03", "status": "completed"},
    )
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Task 3"
    assert data["id"] == task_id


def test_update_task(client):
    # First, create a task
    create_response = client.post(
        "/tasks",
        json={"title": "Test Task 4", "description": "Test Description 4", "due_date": "2024-01-04", "status": "pending"},
    )
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]

    response = client.put(
        f"/tasks/{task_id}",
        json={"title": "Updated Task", "status": "in_progress"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Task"
    assert data["status"] == "in_progress"


def test_delete_task(client):
    # First, create a task
    create_response = client.post(
        "/tasks",
        json={"title": "Test Task 5", "description": "Test Description 5", "due_date": "2024-01-05", "status": "pending"},
    )
    assert create_response.status_code == 200
    task_id = create_response.json()["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200

    # Verify that the task is deleted
    get_response = client.get(f"/tasks/{task_id}")
    assert get_response.status_code == 404
