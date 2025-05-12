#!/usr/bin/env python
"""
Worker Process Launcher

This script launches the worker process for the Research Pack generation system.
It handles command-line arguments, logging setup, and process management.
"""

import argparse
import logging
import os
import sys
import time
import asyncio
from dotenv import load_dotenv

# Import the worker process
from app.services.worker_engine.worker import Worker

# Import the ResearchPackOrchestrator
from research_pack.ResearchPackOrchestrator import ResearchPackOrchestrator
from app.services.document_formatter.document_formatter import DocumentFormatter
from app.services.lily_callout.lily_callout_engine import LilyCalloutEngine

# Import the configuration service
from app.services.config import config_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("worker.log")
    ]
)
logger = logging.getLogger("worker_launcher")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="Launch the worker process")

    parser.add_argument(
        "--worker-id",
        type=str,
        help="Unique identifier for this worker (optional, will generate if not provided)"
    )

    parser.add_argument(
        "--poll-interval",
        type=int,
        default=None,
        help="How often to poll the queue for new jobs (in seconds). If not provided, uses the value from the database."
    )

    parser.add_argument(
        "--max-jobs",
        type=int,
        default=None,
        help="Maximum number of jobs to process in parallel. If not provided, uses the value from the database."
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )

    return parser.parse_args()


async def main():
    """Main entry point for the worker launcher."""
    # Load environment variables
    load_dotenv()

    # Parse command-line arguments
    args = parse_arguments()

    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))

    # Get worker configuration from the database
    worker_config = config_service.get_worker_config()

    # Command-line arguments override database configuration
    max_jobs = args.max_jobs if args.max_jobs is not None else worker_config['max_jobs']
    poll_interval = args.poll_interval if args.poll_interval is not None else worker_config['poll_interval']

    # Initialize the worker
    worker = Worker(
        worker_id=args.worker_id,
        poll_interval=poll_interval,
        max_jobs=max_jobs
    )

    # Initialize components for the ResearchPackOrchestrator
    document_formatter = DocumentFormatter()
    lily_callout_engine = LilyCalloutEngine()

    # Initialize the ResearchPackOrchestrator
    orchestrator = ResearchPackOrchestrator(
        document_formatter=document_formatter,
        lily_callout_engine=lily_callout_engine
    )

    # Define a wrapper function to use the orchestrator
    async def process_research_pack(job, progress_callback):
        # Extract job parameters
        params = job.get('params', {})
        topic = params.get('topic', '')
        key_points = params.get('key_points', [])
        question = key_points[0] if key_points else ''
        education_level = params.get('education_level', 'university')
        include_diagrams = params.get('include_diagrams', True)
        user_id = job.get('user_id')

        # Generate the research pack using the orchestrator
        result = await orchestrator.generate_research_pack(
            topic=topic,
            question=question,
            user_id=user_id,
            education_level=education_level,
            include_diagrams=include_diagrams
        )

        return result

    # Register processors for different job types
    worker.register_processor("research_paper", process_research_pack)

    # Log worker configuration
    logger.info(f"Starting worker with ID {worker.worker_id}")
    logger.info(f"Poll interval: {poll_interval} seconds (from {'command-line' if args.poll_interval else 'database'})")
    logger.info(f"Max jobs: {max_jobs} (from {'command-line' if args.max_jobs else 'database'})")

    try:
        # Start the worker
        await worker.start()
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, stopping worker")
        worker.stop()
    except Exception as e:
        logger.error(f"Error in worker: {str(e)}")
        worker.stop()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
