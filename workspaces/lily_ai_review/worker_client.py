"""
Worker Client - Client for interacting with AI workers
"""
import requests
import json
from typing import Dict, List, Optional, Any

class WorkerClient:
    """Client for interacting with AI workers."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize the client."""
        self.base_url = base_url.rstrip("/")
        self.active_workers = {}

    def activate_worker(self, worker_id: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Activate a worker and get it ready for tasks."""
        url = f"{self.base_url}/api/workers/activate"

        payload = {"worker_id": worker_id}
        if model:
            payload["model"] = model

        response = requests.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        self.active_workers[result["session_id"]] = result

        return result

    def activate_all_workers(self, model: Optional[str] = "google/gemini-2.5-flash-preview") -> List[Dict[str, Any]]:
        """Activate all workers and get them on standby."""
        url = f"{self.base_url}/api/workers/activate-all"

        params = {}
        if model:
            params["model"] = model

        response = requests.post(url, params=params)
        response.raise_for_status()

        results = response.json()
        for worker in results:
            self.active_workers[worker["session_id"]] = worker

        return results

    def assign_task(self, session_id: str, task: str) -> Dict[str, Any]:
        """Assign a task to a worker and get the response."""
        url = f"{self.base_url}/api/workers/task"

        payload = {
            "session_id": session_id,
            "task": task
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()

        result = response.json()
        if session_id in self.active_workers:
            self.active_workers[session_id]["status"] = result["status"]

        return result

    def batch_assign_tasks(self, tasks: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Assign tasks to multiple workers in parallel."""
        url = f"{self.base_url}/api/workers/batch-task"

        payload = {"tasks": tasks}

        response = requests.post(url, json=payload)
        response.raise_for_status()

        results = response.json()
        for session_id, result in results.items():
            if session_id in self.active_workers:
                self.active_workers[session_id]["status"] = result["status"]

        return results

    def get_worker_status(self, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get the status of a specific worker or all workers."""
        url = f"{self.base_url}/api/workers/status"

        params = {}
        if session_id:
            params["session_id"] = session_id

        response = requests.get(url, params=params)
        response.raise_for_status()

        return response.json()

    def deactivate_worker(self, session_id: str) -> Dict[str, Any]:
        """Deactivate a worker."""
        url = f"{self.base_url}/api/workers/deactivate"

        params = {"session_id": session_id}

        response = requests.post(url, params=params)
        response.raise_for_status()

        result = response.json()
        if session_id in self.active_workers:
            del self.active_workers[session_id]

        return result

    def get_active_workers(self) -> Dict[str, Dict[str, Any]]:
        """Get all active workers tracked by this client."""
        return self.active_workers


# Example usage
if __name__ == "__main__":
    import time

    client = WorkerClient()

    print("Activating all workers...")
    workers = client.activate_all_workers()

    print(f"Activated {len(workers)} workers:")
    for worker in workers:
        print(f"- {worker['name']} (Session ID: {worker['session_id']})")

    print("\nAssigning tasks to workers...")
    tasks = {}
    for worker in workers:
        session_id = worker["session_id"]
        worker_id = worker["worker_id"]

        if worker_id == "tool_framework":
            tasks[session_id] = "Create a base Tool class with name, description, and parameters schema properties. Include a method for executing the tool and handling errors."
        elif worker_id == "stripe_customer":
            tasks[session_id] = "Create a tool for retrieving a Stripe customer by ID or email. Include proper error handling and documentation."

    # Only assign tasks to the first two workers for this example
    if tasks:
        results = client.batch_assign_tasks(tasks)

        print("\nTask results:")
        for session_id, result in results.items():
            worker_name = result["name"]
            print(f"\n--- Response from {worker_name} ---")
            print(result["response"][:500] + "..." if len(result["response"]) > 500 else result["response"])

    print("\nDeactivating workers...")
    for worker in workers:
        client.deactivate_worker(worker["session_id"])

    print("All workers deactivated.")
