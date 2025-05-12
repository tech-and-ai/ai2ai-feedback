"""
Queue Manager for the Research Pack generation system.

This module provides functionality to manage the job queue, including
job submission, retrieval, and status updates.
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

import os
from dotenv import load_dotenv

from app.utils.supabase_client import get_supabase_client

# Configure logging
logger = logging.getLogger(__name__)

class QueueManager:
    """
    Manages the job queue for research pack generation.

    This class handles:
    - Job submission
    - Job retrieval based on priority and timestamp
    - Job status updates
    - Parallel job processing limits
    """

    def __init__(self):
        """
        Initialize the queue manager.

        Loads Supabase credentials from environment variables and initializes the client.
        """
        # Load environment variables
        load_dotenv()

        # Maximum number of jobs that can be processed in parallel
        self.max_parallel_jobs = 4

        try:
            # Get the Supabase client
            self.supabase = get_supabase_client()
            
            logger.info("QueueManager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize queue manager: {str(e)}")
            raise

    def submit_job(self, user_id: str, job_type: str, parameters: Dict[str, Any]) -> str:
        """
        Submit a new job to the queue.

        Args:
            user_id: ID of the user submitting the job
            job_type: Type of job (e.g., 'research_pack')
            parameters: Job parameters (topic, question, etc.)

        Returns:
            ID of the created job
        """
        # Generate a unique job ID
        job_id = str(uuid.uuid4())

        try:
            # If Supabase is not available, return a mock job ID
            if self.supabase is None:
                logger.warning(f"Using mock job submission. Job ID: {job_id}")
                return job_id

            # Create a new job with status 'queued' and priority 3
            job_data = {
                'user_id': user_id,
                'job_type': job_type,
                'status': 'queued',
                'priority': 3,
                'params': parameters,
                'job_id': job_id
            }

            # Insert the job into the database
            result = self.supabase.table('saas_job_tracking').insert(job_data).execute()

            # Extract the job ID from the result
            job_id = result.data[0]['job_id']
            logger.info(f"Job {job_id} submitted to queue")

            return job_id

        except Exception as e:
            logger.error(f"Error submitting job: {str(e)}")
            # Return the generated job ID even if there's an error
            logger.warning(f"Returning mock job ID due to error: {job_id}")
            return job_id

    def get_next_jobs(self, worker_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get the next jobs to process based on priority and timestamp.

        Args:
            worker_id: ID of the worker requesting jobs
            limit: Maximum number of jobs to return (defaults to max_parallel_jobs)

        Returns:
            List of jobs to process
        """
        # If Supabase is not available, return an empty list
        if self.supabase is None:
            logger.warning("Cannot get next jobs: Supabase client is not initialized")
            return []

        try:
            # Count how many jobs are currently in progress
            in_progress_count = self.supabase.table('saas_job_tracking') \
                .select('count', count='exact') \
                .eq('status', 'in_progress') \
                .execute()

            # Calculate how many more jobs we can process
            in_progress = in_progress_count.count or 0
            available_slots = max(0, self.max_parallel_jobs - in_progress)

            # If no slots available, return empty list
            if available_slots == 0:
                logger.info(f"No available slots for processing (max {self.max_parallel_jobs} jobs in parallel)")
                return []

            # Use default limit if not provided and adjust based on available slots
            job_limit = self.max_parallel_jobs if limit is None else limit
            job_limit = min(job_limit, available_slots)

            # Get the next jobs to process
            # Order by priority (lowest number first), then created_at (oldest first)
            result = self.supabase.table('saas_job_tracking') \
                .select('*') \
                .eq('status', 'queued') \
                .order('priority') \
                .order('created_at') \
                .limit(job_limit) \
                .execute()

            jobs = result.data

            # Update the status of these jobs to 'in_progress'
            for job in jobs:
                self.update_job_status(job['job_id'], 'in_progress', worker_id)

            logger.info(f"Retrieved {len(jobs)} jobs for processing")
            return jobs

        except Exception as e:
            logger.error(f"Error getting next jobs: {str(e)}")
            return []

    def update_job_status(self, job_id: str, status: str, worker_id: Optional[str] = None,
                         result: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None) -> bool:
        """
        Update the status of a job.

        Args:
            job_id: ID of the job to update
            status: New status ('queued', 'in_progress', 'completed', 'errored')
            worker_id: ID of the worker processing the job (optional)
            result: Job result data (optional)
            error_message: Error message if status is 'errored' (optional)

        Returns:
            True if update was successful, False otherwise
        """
        # If Supabase is not available, return False
        if self.supabase is None:
            logger.warning(f"Cannot update job status: Supabase client is not initialized")
            return False

        try:
            # Prepare update data
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }

            # Add additional fields based on status
            if status == 'in_progress':
                # Set estimated completion time to 10 minutes from now
                update_data['estimated_completion_time'] = (datetime.now() + timedelta(minutes=10)).isoformat()

            elif status == 'completed':
                update_data['completed_at'] = datetime.now().isoformat()
                update_data['priority'] = 0  # Completed jobs have lowest priority
                if result:
                    update_data['result_path'] = result.get('result_path', '')

            elif status == 'errored':
                update_data['priority'] = 2  # Errored jobs have higher priority for reprocessing
                if error_message:
                    update_data['error_message'] = error_message

            # Update the job in the database
            self.supabase.table('saas_job_tracking') \
                .update(update_data) \
                .eq('job_id', job_id) \
                .execute()

            logger.info(f"Job {job_id} status updated to {status}")
            return True

        except Exception as e:
            logger.error(f"Error updating job status: {str(e)}")
            return False

    def resubmit_job(self, job_id: str) -> bool:
        """
        Resubmit a job that previously errored.

        Args:
            job_id: ID of the job to resubmit

        Returns:
            True if resubmission was successful, False otherwise
        """
        try:
            # Get the current job data
            result = self.supabase.table('saas_job_tracking') \
                .select('*') \
                .eq('job_id', job_id) \
                .execute()

            if not result.data:
                logger.error(f"Job {job_id} not found")
                return False

            job = result.data[0]

            # Check if the job is in 'errored' status
            if job['status'] != 'errored':
                logger.error(f"Job {job_id} is not in 'errored' status, cannot resubmit")
                return False

            # Update the job to 'queued' status, keeping priority 2
            update_data = {
                'status': 'queued',
                'error_message': None,
                'worker_id': None
            }

            self.supabase.table('saas_job_tracking') \
                .update(update_data) \
                .eq('job_id', job_id) \
                .execute()

            logger.info(f"Job {job_id} resubmitted")
            return True

        except Exception as e:
            logger.error(f"Error resubmitting job: {str(e)}")
            return False

    def requeue_job(self, job_id: str, retry_count: int, error_message: str = None) -> bool:
        """
        Requeue a job that failed due to SERP API error.

        Args:
            job_id: ID of the job to requeue
            retry_count: Number of retry attempts so far
            error_message: Error message to store

        Returns:
            True if requeue was successful, False otherwise
        """
        try:
            # If Supabase is not available, return False
            if self.supabase is None:
                logger.warning(f"Cannot requeue job: Supabase client is not initialized")
                return False

            # Update the job to 'queued' status, keeping priority 3
            update_data = {
                'status': 'queued',
                'worker_id': None,
                'retry_count': retry_count,
                'updated_at': datetime.now().isoformat()
            }

            # Add error message if provided
            if error_message:
                update_data['error_message'] = error_message

            self.supabase.table('saas_job_tracking') \
                .update(update_data) \
                .eq('job_id', job_id) \
                .execute()

            logger.info(f"Job {job_id} requeued (retry {retry_count})")
            return True

        except Exception as e:
            logger.error(f"Error requeuing job: {str(e)}")
            return False

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status and details of a job.

        Args:
            job_id: ID of the job to check

        Returns:
            Job details including status, or None if job not found
        """
        try:
            result = self.supabase.table('saas_job_tracking') \
                .select('*') \
                .eq('job_id', job_id) \
                .execute()

            if not result.data:
                logger.warning(f"Job {job_id} not found")
                return None

            return result.data[0]

        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return None

    def get_user_jobs(self, user_id: str, limit: int = 10, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get jobs for a specific user.

        Args:
            user_id: ID of the user
            limit: Maximum number of jobs to return
            status: Filter by status (optional)

        Returns:
            List of jobs for the user
        """
        try:
            # If Supabase is not available, return a mock job
            if self.supabase is None:
                # Create a mock job for testing purposes
                mock_job = {
                    'job_id': str(uuid.uuid4()),
                    'user_id': user_id,
                    'job_type': 'research_paper',
                    'status': 'queued',
                    'priority': 3,
                    'created_at': datetime.now().isoformat(),
                    'params': {
                        'custom_title': 'Your Research Paper',
                        'topic': 'Your research topic',
                        'education_level': 'undergraduate',
                        'include_diagrams': True,
                        'include_research': True,
                        'key_points': ['Your key points']
                    }
                }
                logger.warning(f"Returning mock job data for user {user_id}")
                return [mock_job]

            query = self.supabase.table('saas_job_tracking') \
                .select('*') \
                .eq('user_id', user_id) \
                .order('created_at', desc=True) \
                .limit(limit)

            if status:
                query = query.eq('status', status)

            result = query.execute()

            return result.data

        except Exception as e:
            logger.error(f"Error getting user jobs: {str(e)}")
            # Return a mock job in case of error
            mock_job = {
                'job_id': str(uuid.uuid4()),
                'user_id': user_id,
                'job_type': 'research_paper',
                'status': 'queued',
                'created_at': datetime.now().isoformat(),
                'params': {
                    'custom_title': 'Your Research Paper',
                    'topic': 'Your research topic'
                }
            }
            return [mock_job]

    def update_job_progress(self, job_id: str, progress: float, progress_message: Optional[str] = None) -> bool:
        """
        Update the progress of a job.

        Args:
            job_id: ID of the job to update
            progress: Progress value (0-100)
            progress_message: Progress message (optional)

        Returns:
            True if update was successful, False otherwise
        """
        # If Supabase is not available, return False
        if self.supabase is None:
            logger.warning(f"Cannot update job progress: Supabase client is not initialized")
            return False

        try:
            # Create update data
            update_data = {
                'progress': progress,
                'updated_at': datetime.now().isoformat()
            }

            # Add progress message if provided
            if progress_message:
                update_data['progress_message'] = progress_message

            # Update estimated completion time based on progress
            if progress > 0 and progress < 100:
                # Calculate remaining time based on progress
                # Assume 10 minutes total time, so remaining time is (100 - progress) / 100 * 10 minutes
                remaining_minutes = (100 - progress) / 100 * 10
                update_data['estimated_completion_time'] = (datetime.now() + timedelta(minutes=remaining_minutes)).isoformat()

            # Update the job in the database
            self.supabase.table('saas_job_tracking') \
                .update(update_data) \
                .eq('job_id', job_id) \
                .execute()

            logger.info(f"Job {job_id} progress updated to {progress}%")
            return True

        except Exception as e:
            logger.error(f"Error updating job progress: {str(e)}")
            return False

    def clean_completed_jobs(self, days_old: int = 30) -> int:
        """
        Remove completed jobs older than the specified number of days.

        Args:
            days_old: Remove jobs older than this many days

        Returns:
            Number of jobs removed
        """
        try:
            # Calculate the cutoff date
            cutoff_date = datetime.now() - timedelta(days=days_old)

            # Delete completed jobs older than the cutoff date
            result = self.supabase.table('saas_job_tracking') \
                .delete() \
                .eq('status', 'completed') \
                .lt('completed_at', cutoff_date.isoformat()) \
                .execute()

            count = len(result.data)
            logger.info(f"Removed {count} completed jobs older than {days_old} days")

            return count

        except Exception as e:
            logger.error(f"Error cleaning completed jobs: {str(e)}")
            return 0

# Example usage
if __name__ == "__main__":
    # This is just an example of how to use the Queue Manager
    # In a real application, you would initialize it with actual Supabase credentials

    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        # Initialize the queue manager
        queue_manager = QueueManager()

        # Submit a test job
        job_id = queue_manager.submit_job(
            user_id="test_user",
            job_type="research_pack",
            parameters={
                "topic": "Artificial Intelligence Ethics",
                "question": "What are the key ethical considerations in AI development?",
                "education_level": "university"
            }
        )

        print(f"Submitted job: {job_id}")

        # Get the next job to process
        jobs = queue_manager.get_next_jobs(worker_id="test_worker")

        if jobs:
            print(f"Next job to process: {jobs[0]['job_id']}")

            # Update the job status to completed
            queue_manager.update_job_status(
                job_id=jobs[0]['job_id'],
                status="completed",
                result={"docx_url": "https://example.com/document.docx", "pdf_url": "https://example.com/document.pdf"}
            )

            print(f"Job {jobs[0]['job_id']} marked as completed")

    except Exception as e:
        print(f"Error: {str(e)}")
