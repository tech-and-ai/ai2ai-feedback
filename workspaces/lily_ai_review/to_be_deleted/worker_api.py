"""
Worker API - FastAPI endpoints for managing AI workers
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import os
import json
import asyncio
from worker_manager import WorkerManager

app = FastAPI(
    title="AI Worker API",
    description="API for managing AI workers for delegated tasks",
    version="1.0.0",
)

# Initialize worker manager
worker_manager = WorkerManager()

# Pydantic models
class ActivateWorkerRequest(BaseModel):
    worker_id: str
    model: Optional[str] = "google/gemini-2.5-flash-preview"
    worker_name: Optional[str] = None

class TaskRequest(BaseModel):
    session_id: str
    task: str

class BatchTaskRequest(BaseModel):
    tasks: Dict[str, str]  # Map of session_id to task

class WorkerResponse(BaseModel):
    session_id: str
    worker_id: str
    name: str
    status: str
    message: Optional[str] = None
    response: Optional[str] = None

# API endpoints
@app.post("/api/workers/activate", response_model=WorkerResponse)
async def activate_worker(request: ActivateWorkerRequest):
    """Activate a worker and get it ready for tasks."""
    try:
        result = await worker_manager.activate_worker(request.worker_id, request.model)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activating worker: {str(e)}")

@app.post("/api/workers/activate-all", response_model=List[WorkerResponse])
async def activate_all_workers(model: Optional[str] = "google/gemini-2.5-flash-preview"):
    """Activate all workers and get them on standby."""
    try:
        results = await worker_manager.activate_all_workers(model)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error activating workers: {str(e)}")

@app.post("/api/workers/task", response_model=WorkerResponse)
async def assign_task(request: TaskRequest):
    """Assign a task to a worker and get the response."""
    try:
        result = await worker_manager.assign_task(request.session_id, request.task)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error assigning task: {str(e)}")

@app.post("/api/workers/batch-task", response_model=Dict[str, WorkerResponse])
async def batch_assign_tasks(request: BatchTaskRequest):
    """Assign tasks to multiple workers in parallel."""
    results = {}
    tasks = []

    for session_id, task in request.tasks.items():
        tasks.append(worker_manager.assign_task(session_id, task))

    # Execute tasks in parallel
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # Process responses
    for i, (session_id, _) in enumerate(request.tasks.items()):
        response = responses[i]
        if isinstance(response, Exception):
            results[session_id] = {
                "session_id": session_id,
                "worker_id": "unknown",
                "name": "unknown",
                "status": "error",
                "message": f"Error: {str(response)}"
            }
        else:
            results[session_id] = response

    return results

@app.get("/api/workers/status")
async def get_worker_status(session_id: Optional[str] = None):
    """Get the status of a specific worker or all workers."""
    try:
        return worker_manager.get_worker_status(session_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting worker status: {str(e)}")

@app.post("/api/workers/deactivate", response_model=WorkerResponse)
async def deactivate_worker(session_id: str):
    """Deactivate a worker."""
    try:
        result = await worker_manager.deactivate_worker(session_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating worker: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("worker_api:app", host="0.0.0.0", port=8000, reload=True)
