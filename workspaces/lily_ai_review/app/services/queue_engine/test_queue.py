"""
Test script for the queue system.

This script tests the queue manager by submitting a job and retrieving it.
"""
import os
import sys
import logging
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

# Import the queue manager
from app.services.queue_engine.queue_manager import QueueManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_queue():
    """Test the queue manager."""
    logger.info("Testing Queue Manager")
    
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
        
        logger.info(f"Submitted job: {job_id}")
        
        # Get the next job to process
        jobs = queue_manager.get_next_jobs(worker_id="test_worker")
        
        if jobs:
            logger.info(f"Next job to process: {jobs[0]['job_id']}")
            
            # Update the job status to completed
            queue_manager.update_job_status(
                job_id=jobs[0]['job_id'],
                status="completed",
                result={"docx_url": "https://example.com/document.docx", "pdf_url": "https://example.com/document.pdf"}
            )
            
            logger.info(f"Job {jobs[0]['job_id']} marked as completed")
        
        # Get the job status
        job_status = queue_manager.get_job_status(job_id)
        logger.info(f"Job status: {job_status}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_queue())
    sys.exit(0 if success else 1)
