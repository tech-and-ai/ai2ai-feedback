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

# Import the worker process and queue manager
from app.services.queue_engine.worker import Worker
from app.services.queue_engine.queue_manager import QueueManager

# Import the ResearchPackOrchestrator
from research_pack.ResearchPackOrchestrator import ResearchPackOrchestrator
from app.services.document_formatter.document_formatter import DocumentFormatter
from app.services.lily_callout.lily_callout_engine import LilyCalloutEngine

# Import the diagram orchestrator
try:
    from diagram_orchestrator.orchestrator import (
        generate_mind_map,
        generate_research_journey_map,
        generate_question_breakdown,
        generate_argument_map,
        generate_comparative_analysis
    )
    DIAGRAM_ORCHESTRATOR_AVAILABLE = True
except ImportError:
    logger.warning("Diagram orchestrator not available. Diagrams will not be generated.")
    DIAGRAM_ORCHESTRATOR_AVAILABLE = False

# Import the content generator
try:
    from diagram_orchestrator.content_generator import ContentGenerator as DiagramContentGenerator
    CONTENT_GENERATOR_AVAILABLE = True
except ImportError:
    logger.warning("Content generator not available. Content will not be generated.")
    CONTENT_GENERATOR_AVAILABLE = False

# Import the research generator
try:
    from app.services.research_generator.research_generator import ResearchGenerator
    RESEARCH_GENERATOR_AVAILABLE = True
except ImportError:
    logger.warning("Research generator not available. Research will not be conducted.")
    RESEARCH_GENERATOR_AVAILABLE = False

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

    # Initialize queue manager
    queue_manager = QueueManager()

    # Initialize components for the ResearchPackOrchestrator
    document_formatter = DocumentFormatter()
    lily_callout_engine = LilyCalloutEngine()

    # Get API keys from environment
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    serp_key = os.getenv("SERP_API_KEY")

    # Initialize content generator if available
    content_generator = None
    if CONTENT_GENERATOR_AVAILABLE:
        try:
            content_generator = DiagramContentGenerator(openrouter_key=openrouter_key)
            logger.info("Content generator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing content generator: {str(e)}")

    # Initialize diagram orchestrator if available
    diagram_orchestrator = None
    if DIAGRAM_ORCHESTRATOR_AVAILABLE and content_generator:
        try:
            # Create a simple wrapper class to match the interface expected by ResearchPackOrchestrator
            class DiagramOrchestratorWrapper:
                def __init__(self, content_generator):
                    self.content_generator = content_generator

                async def generate_mind_map(self, topic):
                    return generate_mind_map(topic)

                async def generate_journey_map(self, topic):
                    return generate_research_journey_map(topic)

                async def generate_question_breakdown(self, question):
                    return generate_question_breakdown(question)

                async def generate_argument_mapping(self, topic):
                    return generate_argument_map(topic)

                async def generate_comparative_analysis(self, topic):
                    return generate_comparative_analysis(topic)

            diagram_orchestrator = DiagramOrchestratorWrapper(content_generator)
            logger.info("Diagram orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing diagram orchestrator: {str(e)}")

    # Initialize research generator if available
    research_generator = None
    if RESEARCH_GENERATOR_AVAILABLE:
        try:
            research_generator = ResearchGenerator(
                openrouter_key=openrouter_key,
                serp_api_key=serp_key
            )
            logger.info("Research generator initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing research generator: {str(e)}")

    # Initialize the ResearchPackOrchestrator with all available components
    orchestrator = ResearchPackOrchestrator(
        document_formatter=document_formatter,
        lily_callout_engine=lily_callout_engine,
        diagram_orchestrator=diagram_orchestrator,
        content_generator=content_generator,
        openrouter_key=openrouter_key,
        serp_key=serp_key
    )

    # Initialize the worker
    worker = Worker(
        queue_manager=queue_manager,
        research_pack_orchestrator=orchestrator,
        worker_id=args.worker_id,
        poll_interval=poll_interval,
        max_parallel_jobs=max_jobs
    )

    # The worker class already has the logic to process research_paper jobs
    # No need to register a processor

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
