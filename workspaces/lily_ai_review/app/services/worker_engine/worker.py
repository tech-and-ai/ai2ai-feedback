"""
Worker process module for the Research Pack generation system.

This module provides functionality to process jobs from the queue,
including job retrieval, processing, and status updates.
"""

import logging
import time
import uuid
import os
import signal
import sys
import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

# Import the queue manager
from app.services.queue_engine.queue_manager import QueueManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Worker:
    """
    Worker process for processing jobs from the queue.

    This class provides functionality to:
    - Poll the queue for new jobs
    - Process jobs
    - Update job status
    - Handle errors
    """

    def __init__(self,
                 worker_id: Optional[str] = None,
                 poll_interval: int = 5,
                 max_jobs: int = 1,
                 processors: Dict[str, Callable] = None):
        """
        Initialize the worker process.

        Args:
            worker_id: Unique identifier for this worker (optional, will generate if not provided)
            poll_interval: How often to poll the queue for new jobs (in seconds)
            max_jobs: Maximum number of jobs to process in parallel
            processors: Dictionary mapping job types to processor functions
        """
        # Generate a worker ID if not provided
        self.worker_id = worker_id or f"worker-{uuid.uuid4()}"

        # Set polling interval and max jobs
        self.poll_interval = poll_interval
        self.max_jobs = max_jobs

        # Initialize the queue manager
        self.queue_manager = QueueManager()

        # Initialize job processors
        self.processors = processors or {}

        # Initialize running flag
        self.running = False

        # Initialize active jobs
        self.active_jobs = {}

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._handle_signal)
        signal.signal(signal.SIGTERM, self._handle_signal)

        logger.info(f"Worker {self.worker_id} initialized with poll interval {poll_interval}s and max jobs {max_jobs}")

    def register_processor(self, job_type: str, processor: Callable):
        """
        Register a processor function for a specific job type.

        Args:
            job_type: Type of job to register processor for
            processor: Function to process jobs of this type
        """
        self.processors[job_type] = processor
        logger.info(f"Registered processor for job type {job_type}")

    async def start(self):
        """
        Start the worker process.

        This method will start polling the queue for new jobs and processing them.
        """
        logger.info(f"Starting worker {self.worker_id}")
        self.running = True

        try:
            while self.running:
                # Check for new jobs if we have capacity
                if len(self.active_jobs) < self.max_jobs:
                    self._poll_queue()

                # Process active jobs
                await self._process_active_jobs()

                # Sleep for the polling interval
                await asyncio.sleep(self.poll_interval)
        except Exception as e:
            logger.error(f"Error in worker main loop: {str(e)}")
            self.running = False

        logger.info(f"Worker {self.worker_id} stopped")

    def stop(self):
        """
        Stop the worker process.

        This method will stop the worker process gracefully.
        """
        logger.info(f"Stopping worker {self.worker_id}")
        self.running = False

    def _handle_signal(self, signum, frame):
        """
        Handle signals (SIGINT, SIGTERM).

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info(f"Received signal {signum}, stopping worker")
        self.stop()
        sys.exit(0)

    def _poll_queue(self):
        """
        Poll the queue for new jobs.

        This method will check for new jobs and add them to the active jobs list.
        """
        try:
            # Calculate how many more jobs we can process
            available_slots = self.max_jobs - len(self.active_jobs)

            if available_slots <= 0:
                return

            # Get next jobs from the queue
            jobs = self.queue_manager.get_next_jobs(self.worker_id, limit=available_slots)

            if not jobs:
                return

            logger.info(f"Retrieved {len(jobs)} new jobs from queue")

            # Add jobs to active jobs
            for job in jobs:
                job_id = job.get('job_id')
                job_type = job.get('job_type')

                if job_type not in self.processors:
                    logger.warning(f"No processor registered for job type {job_type}, skipping job {job_id}")
                    self.queue_manager.update_job_status(
                        job_id=job_id,
                        status='errored',
                        worker_id=self.worker_id,
                        error_message=f"No processor registered for job type {job_type}"
                    )
                    continue

                logger.info(f"Adding job {job_id} of type {job_type} to active jobs")
                self.active_jobs[job_id] = {
                    'job': job,
                    'status': 'in_progress',
                    'start_time': datetime.now(),
                    'progress': 0
                }

                # Update job status to in_progress
                self.queue_manager.update_job_status(
                    job_id=job_id,
                    status='in_progress',
                    worker_id=self.worker_id
                )
        except Exception as e:
            logger.error(f"Error polling queue: {str(e)}")

    async def _process_active_jobs(self):
        """
        Process active jobs.

        This method will process all active jobs and update their status.
        """
        # Get a list of job IDs to avoid modifying the dictionary during iteration
        job_ids = list(self.active_jobs.keys())

        for job_id in job_ids:
            if job_id not in self.active_jobs:
                continue

            job_data = self.active_jobs[job_id]
            job = job_data['job']
            job_type = job.get('job_type')

            # Skip jobs that are already completed or errored
            if job_data['status'] in ['completed', 'errored']:
                continue

            try:
                # Get the processor for this job type
                processor = self.processors.get(job_type)

                if not processor:
                    logger.warning(f"No processor registered for job type {job_type}, skipping job {job_id}")
                    job_data['status'] = 'errored'
                    self.queue_manager.update_job_status(
                        job_id=job_id,
                        status='errored',
                        worker_id=self.worker_id,
                        error_message=f"No processor registered for job type {job_type}"
                    )
                    continue

                # Process the job
                logger.info(f"Processing job {job_id} of type {job_type}")

                # Call the processor with the job data and a callback for progress updates
                result = await processor(
                    job=job,
                    progress_callback=lambda progress, message: self._update_progress(job_id, progress, message)
                )

                # Check if the job should be requeued (e.g., SERP API error with retry)
                if isinstance(result, dict) and result.get('should_requeue', False):
                    # Get the retry count
                    retry_count = result.get('retry_count', 1)
                    error_message = result.get('error', 'Unknown error')

                    logger.warning(f"Job {job_id} needs to be requeued (retry {retry_count}): {error_message}")

                    # Update job status to queued and increment retry count
                    job_data['status'] = 'requeued'
                    job_data['end_time'] = datetime.now()

                    # Requeue the job with the same priority
                    self.queue_manager.requeue_job(
                        job_id=job_id,
                        retry_count=retry_count,
                        error_message=error_message
                    )

                    # Remove job from active jobs
                    del self.active_jobs[job_id]
                else:
                    # Update job status to completed
                    logger.info(f"Job {job_id} completed successfully")
                    job_data['status'] = 'completed'
                    job_data['result'] = result
                    job_data['end_time'] = datetime.now()

                    self.queue_manager.update_job_status(
                        job_id=job_id,
                        status='completed',
                        worker_id=self.worker_id,
                        result=result
                    )

                    # Remove job from active jobs
                    del self.active_jobs[job_id]

            except Exception as e:
                logger.error(f"Error processing job {job_id}: {str(e)}")
                job_data['status'] = 'errored'
                job_data['error'] = str(e)
                job_data['end_time'] = datetime.now()

                self.queue_manager.update_job_status(
                    job_id=job_id,
                    status='errored',
                    worker_id=self.worker_id,
                    error_message=str(e)
                )

                # Remove job from active jobs
                del self.active_jobs[job_id]

    def _update_progress(self, job_id: str, progress: float, message: str):
        """
        Update job progress.

        Args:
            job_id: ID of the job to update
            progress: Progress value (0-100)
            message: Progress message
        """
        if job_id not in self.active_jobs:
            return

        # Update progress in active jobs
        self.active_jobs[job_id]['progress'] = progress

        # Update progress in queue
        self.queue_manager.update_job_progress(
            job_id=job_id,
            progress=progress,
            progress_message=message
        )
