"""
Worker Agent Initialization

This module initializes worker agents on application startup.
"""

import logging
import uuid
import asyncio
from typing import List, Optional, Dict

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import Agent, async_session
from .worker_agent import WorkerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("worker-init")

# Global worker agent instances
worker_instances: Dict[str, WorkerAgent] = {}

# Worker agent definitions with role-specific model assignments
WORKER_DEFINITIONS = [
    # Designer/Architect - Analyzes requirements and creates design specifications
    # Uses Gemma 3 4B for architecture and design tasks
    {
        "name": "Designer",
        "role": "Designer",
        "skills": ["requirements", "analysis", "design", "architecture", "database", "api", "ui", "ux"],
        "model": "gemma3:4b",
        "agent_type": "worker",
        "max_workload": 5
    },

    # Coder - Implements the design into working code
    # Uses DeepSeek Coder v2 for code implementation tasks
    {
        "name": "Coder",
        "role": "Developer",
        "skills": ["python", "javascript", "backend", "frontend", "development", "database", "api", "integration"],
        "model": "deepseek-coder-v2:16b",
        "agent_type": "worker",
        "max_workload": 5
    },

    # Tester - Verifies the implementation against requirements
    # Uses DeepSeek Coder v2 for testing tasks
    {
        "name": "Tester",
        "role": "Tester",
        "skills": ["testing", "quality", "python", "javascript", "unit", "integration", "acceptance"],
        "model": "deepseek-coder-v2:16b",
        "agent_type": "worker",
        "max_workload": 5
    },

    # Reviewer - Reviews the work and provides feedback
    # Uses Gemma 3 4B for review tasks
    {
        "name": "Reviewer",
        "role": "Reviewer",
        "skills": ["review", "documentation", "quality", "architecture", "design", "development", "testing"],
        "model": "gemma3:4b",
        "agent_type": "worker",
        "max_workload": 5
    },

    # Documenter - Creates documentation for the project
    # Uses Gemma 3 1B for documentation tasks
    {
        "name": "Documenter",
        "role": "Writer",
        "skills": ["documentation", "writing", "technical", "markdown", "user-guide"],
        "model": "gemma3:1b",
        "agent_type": "worker",
        "max_workload": 5
    }
]

async def get_or_create_worker_agents(db: AsyncSession) -> List[Agent]:
    """
    Get or create worker agents

    Args:
        db: Database session

    Returns:
        List[Agent]: Worker agents
    """
    workers = []

    for worker_def in WORKER_DEFINITIONS:
        # Check if worker agent exists with these skills
        query = select(Agent).where(
            Agent.name == worker_def["name"],
            Agent.agent_type == "worker"
        )
        result = await db.execute(query)
        worker = result.scalars().first()

        if worker:
            logger.info(f"Found existing worker agent: {worker.name} ({worker.agent_id})")
            workers.append(worker)
        else:
            # Create worker agent
            worker = Agent(
                agent_id=str(uuid.uuid4()),
                session_id="worker_session",
                agent_index=len(workers),
                name=worker_def["name"],
                role=worker_def["role"],
                skills=",".join(worker_def["skills"]),
                model=worker_def["model"],
                status="idle",
                agent_type=worker_def["agent_type"],
                current_workload=0,
                max_workload=worker_def["max_workload"]
            )
            db.add(worker)
            await db.commit()

            logger.info(f"Created new worker agent: {worker.name} ({worker.agent_id})")
            workers.append(worker)

    return workers

async def start_worker_agents():
    """
    Start worker agents

    Returns:
        bool: True if successful, False otherwise
    """
    global worker_instances

    try:
        # Get database session
        async with async_session() as db:
            # Get or create worker agents
            workers = await get_or_create_worker_agents(db)

            # Create worker agent instances
            for worker in workers:
                # Create worker agent instance
                skills = worker.skills.split(",") if worker.skills else []

                # Get endpoint from performance_metrics if available
                endpoint = None
                try:
                    if worker.performance_metrics:
                        performance_metrics = json.loads(worker.performance_metrics)
                        endpoint = performance_metrics.get("endpoint")
                except:
                    logger.warning(f"Failed to parse performance_metrics for worker {worker.name}")

                worker_instance = WorkerAgent(
                    worker.agent_id,
                    worker.name,
                    worker.role,
                    worker.model,
                    skills,
                    endpoint
                )

                # Start worker agent
                await worker_instance.start()

                # Update agent status
                worker.status = "running"

                # Store worker instance
                worker_instances[worker.agent_id] = worker_instance

            await db.commit()

            logger.info(f"Started {len(workers)} worker agents")
            return True
    except Exception as e:
        logger.error(f"Error starting worker agents: {e}")
        return False

async def stop_worker_agents():
    """
    Stop worker agents

    Returns:
        bool: True if successful, False otherwise
    """
    global worker_instances

    try:
        # Get database session
        async with async_session() as db:
            # Stop worker agent instances
            for agent_id, worker_instance in worker_instances.items():
                # Stop worker agent
                await worker_instance.stop()

                # Update agent status
                query = select(Agent).where(
                    Agent.agent_id == agent_id
                )
                result = await db.execute(query)
                worker = result.scalars().first()

                if worker:
                    worker.status = "idle"

            await db.commit()

        worker_instances = {}
        logger.info("Worker agents stopped")
        return True
    except Exception as e:
        logger.error(f"Error stopping worker agents: {e}")
        return False
