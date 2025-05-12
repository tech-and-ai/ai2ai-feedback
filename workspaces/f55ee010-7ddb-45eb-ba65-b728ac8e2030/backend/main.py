
from fastapi import FastAPI, HTTPException, Depends
from typing import List
from datetime import date
from .models import Task, TaskCreate, TaskUpdate, TaskStatus
from .database import get_db, SessionLocal
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date, Enum
import enum
from sqlalchemy.orm import sessionmaker
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS configuration to allow requests from the frontend
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",  # Assuming frontend runs on port 3000
    "http://localhost:8080",
    "*",  # WARNING: This allows all origins, use with caution in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = "sqlite:///./tasks.db"  # SQLite database file
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.pending)

Base.metadata.create_all(bind=engine)

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/tasks", response_model=List[Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    tasks = db.query(TaskDB).offset(skip).limit(limit).all()
    return tasks


@app.post("/tasks", response_model=Task)
def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    db_task = TaskDB(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks/{task_id}", response_model=Task)
def read_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@app.put("/tasks/{task_id}", response_model=Task)
def update_task(task_id: int, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    for key, value in task.dict(exclude_unset=True).items():
        setattr(db_task, key, value)

    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", response_model=Task)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    db_task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return db_task
