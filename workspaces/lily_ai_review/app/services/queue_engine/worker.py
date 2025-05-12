"""
Worker for processing jobs from the queue.

This module provides a worker that processes jobs from the queue,
coordinating with the Research Pack Orchestrator to generate research packs.
"""

import logging
import asyncio
import os
import time
import uuid
import signal
import sys
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from app.services.queue_engine.queue_manager import QueueManager
from research_pack.ResearchPackOrchestrator import ResearchPackOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("worker.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("worker")

class Worker:
    """
    Worker for processing jobs from the queue.

    This class:
    - Retrieves jobs from the queue
    - Processes jobs using the Research Pack Orchestrator
    - Updates job status in the queue
    - Handles errors and retries
    """

    def __init__(
            self,
            queue_manager: QueueManager,
            research_pack_orchestrator: ResearchPackOrchestrator,
            worker_id: Optional[str] = None,
            poll_interval: int = 5,
            max_parallel_jobs: int = 4
        ):
        """
        Initialize the worker.

        Args:
            queue_manager: Queue manager for retrieving and updating jobs
            research_pack_orchestrator: Orchestrator for generating research packs
            worker_id: ID of this worker (optional, will generate if not provided)
            poll_interval: How often to poll for new jobs (in seconds)
            max_parallel_jobs: Maximum number of jobs to process in parallel
        """
        self.queue_manager = queue_manager
        self.orchestrator = research_pack_orchestrator
        self.worker_id = worker_id or f"worker-{uuid.uuid4()}"
        self.poll_interval = poll_interval
        self.max_parallel_jobs = max_parallel_jobs
        self.running = False
        self.current_jobs = {}  # job_id -> task

        logger.info(f"Worker {self.worker_id} initialized")

    async def start(self):
        """
        Start the worker.
        """
        logger.info(f"Worker {self.worker_id} starting")
        self.running = True

        # Set up signal handlers for graceful shutdown
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._signal_handler)

        # Main worker loop
        while self.running:
            try:
                # Check if we can process more jobs
                available_slots = self.max_parallel_jobs - len(self.current_jobs)

                if available_slots > 0:
                    # Get next jobs from the queue
                    jobs = self.queue_manager.get_next_jobs(self.worker_id, limit=available_slots)

                    # Process each job
                    for job in jobs:
                        # Start a task for each job
                        task = asyncio.create_task(self._process_job(job))
                        self.current_jobs[job['job_id']] = task
                        logger.info(f"Started processing job {job['job_id']}")

                # Clean up completed tasks
                self._cleanup_completed_tasks()

                # Wait before polling again
                await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error in worker loop: {str(e)}")
                await asyncio.sleep(self.poll_interval)

        logger.info(f"Worker {self.worker_id} stopped")

    def stop(self):
        """
        Stop the worker gracefully.
        """
        logger.info(f"Worker {self.worker_id} stopping")
        self.running = False

    def _signal_handler(self, sig, frame):
        """
        Handle signals for graceful shutdown.
        """
        logger.info(f"Received signal {sig}, shutting down")
        self.stop()

    def _cleanup_completed_tasks(self):
        """
        Clean up completed tasks.
        """
        completed_jobs = []

        for job_id, task in list(self.current_jobs.items()):
            if task.done():
                try:
                    # Get the result (and propagate any exceptions)
                    task.result()
                except Exception as e:
                    logger.error(f"Task for job {job_id} failed: {str(e)}")

                # Remove from current jobs
                completed_jobs.append(job_id)

        # Remove completed jobs from the dictionary
        for job_id in completed_jobs:
            del self.current_jobs[job_id]

    async def _process_job(self, job: Dict[str, Any]):
        """
        Process a single job.

        Args:
            job: The job to process
        """
        job_id = job['job_id']
        logger.info(f"Processing job {job_id}")

        try:
            # Extract job parameters
            parameters = job.get('params', {})  # Use 'params' instead of 'parameters'
            user_id = job['user_id']

            # Process based on job type
            if job['job_type'] == 'research_pack' or job['job_type'] == 'research_paper':
                # Generate research pack
                result = await self.orchestrator.generate_research_pack(
                    topic=parameters.get('topic', ''),
                    question=parameters.get('question', ''),
                    user_id=user_id,
                    education_level=parameters.get('education_level', 'university'),
                    include_diagrams=parameters.get('include_diagrams', True),
                    premium=parameters.get('premium', False)
                )

                # Update job status to completed
                self.queue_manager.update_job_status(
                    job_id=job_id,
                    status='completed',
                    result={
                        'docx_path': result.get('document_path'),
                        'pdf_path': result.get('pdf_path'),
                        'docx_url': result.get('docx_url'),
                        'pdf_url': result.get('pdf_url'),
                        'generation_time': result.get('generation_time')
                    }
                )

                logger.info(f"Job {job_id} completed successfully")

            else:
                # Unsupported job type
                logger.error(f"Unsupported job type: {job['job_type']}")
                self.queue_manager.update_job_status(
                    job_id=job_id,
                    status='errored',
                    error_message=f"Unsupported job type: {job['job_type']}"
                )

        except Exception as e:
            logger.error(f"Error processing job {job_id}: {str(e)}")

            # Update job status to errored
            self.queue_manager.update_job_status(
                job_id=job_id,
                status='errored',
                error_message=str(e)
            )

        finally:
            # Remove from current jobs
            if job_id in self.current_jobs:
                del self.current_jobs[job_id]

# Worker daemon that runs as a background service
class WorkerDaemon:
    """
    Daemon for running the worker as a background service.
    """

    def __init__(
            self,
            queue_manager: Optional[QueueManager] = None,
            research_pack_orchestrator: Optional[ResearchPackOrchestrator] = None,
            worker_id: Optional[str] = None,
            poll_interval: int = 5,
            max_parallel_jobs: int = 4
        ):
        """
        Initialize the worker daemon.

        Args:
            queue_manager: Queue manager for retrieving and updating jobs
            research_pack_orchestrator: Orchestrator for generating research packs
            worker_id: ID of this worker (optional, will generate if not provided)
            poll_interval: How often to poll for new jobs (in seconds)
            max_parallel_jobs: Maximum number of jobs to process in parallel
        """
        # Initialize queue manager if not provided
        if queue_manager is None:
            try:
                queue_manager = QueueManager()
                logger.info("Queue manager initialized")
            except Exception as e:
                logger.error(f"Error initializing queue manager: {str(e)}")
                raise

        # Initialize research pack orchestrator if not provided
        if research_pack_orchestrator is None:
            try:
                # Import here to avoid circular imports
                from app.services.document_formatter.document_formatter import DocumentFormatter
                from app.services.lily_callout.lily_callout_engine import LilyCalloutEngine

                # Initialize components
                document_formatter = DocumentFormatter()
                lily_callout_engine = LilyCalloutEngine()

                # Initialize orchestrator
                research_pack_orchestrator = ResearchPackOrchestrator(
                    document_formatter=document_formatter,
                    lily_callout_engine=lily_callout_engine
                )

                logger.info("Research pack orchestrator initialized")
            except Exception as e:
                logger.error(f"Error initializing research pack orchestrator: {str(e)}")
                raise

        # Initialize worker
        self.worker = Worker(
            queue_manager=queue_manager,
            research_pack_orchestrator=research_pack_orchestrator,
            worker_id=worker_id,
            poll_interval=poll_interval,
            max_parallel_jobs=max_parallel_jobs
        )

        logger.info("Worker daemon initialized")

    async def run(self):
        """
        Run the worker daemon.
        """
        logger.info("Worker daemon starting")

        try:
            await self.worker.start()
        except Exception as e:
            logger.error(f"Error in worker daemon: {str(e)}")

        logger.info("Worker daemon stopped")

# Example usage
if __name__ == "__main__":
    # This is just an example of how to run the worker daemon
    # In a real application, you would initialize it with actual components

    try:
        # Initialize the worker daemon
        daemon = WorkerDaemon()

        # Run the daemon
        asyncio.run(daemon.run())

    except Exception as e:
        logger.error(f"Error: {str(e)}")
