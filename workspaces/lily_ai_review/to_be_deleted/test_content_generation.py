"""
Test Content Generation

This script tests the integration between the Research Pack Orchestrator
and the content generation components.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any

# Import the necessary components
from app.services.lily_callout.lily_callout_engine import LilyCalloutEngine
from app.services.document_formatter.document_formatter import DocumentFormatter
from research_pack.ResearchPackOrchestrator import ResearchPackOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_content_generation():
    """
    Test the content generation integration.
    """
    # Step 1: Set up the test parameters
    topic = "Climate change impacts on marine ecosystems"
    question = "How does ocean acidification affect coral reefs?"
    user_id = "test_user"
    education_level = "university"
    premium = False

    # Get API keys from environment variables
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    serp_key = os.getenv("SERP_API_KEY")

    if not openrouter_key:
        logger.error("OpenRouter API key not found in environment variables")
        return

    # Step 2: Initialize the components
    logger.info("Initializing components...")

    # Initialize the Lily callout engine
    lily_callout_engine = LilyCalloutEngine(
        openrouter_api_key=openrouter_key
    )

    # Initialize the document formatter
    document_formatter = DocumentFormatter()

    # Initialize the orchestrator
    orchestrator = ResearchPackOrchestrator(
        lily_callout_engine=lily_callout_engine,
        document_formatter=document_formatter,
        openrouter_key=openrouter_key,
        serp_key=serp_key
    )

    # Step 3: Generate content
    logger.info("Generating content...")
    content = await orchestrator._generate_content(
        topic=topic,
        question=question,
        education_level=education_level,
        premium=premium
    )

    # Step 4: Process content through Lily callout engine
    logger.info("Processing content through Lily callout engine...")
    enhanced_content = await orchestrator._process_with_lily_callout_engine(
        content=content,
        topic=topic,
        education_level=education_level
    )

    # Step 5: Format the document
    logger.info("Formatting document...")
    document_path = await orchestrator._format_document(
        content=enhanced_content,
        topic=topic,
        user_id=user_id,
        diagrams=[],
        question=question
    )

    logger.info(f"Document saved to {document_path}")
    logger.info("Content generation test completed successfully")
    return document_path

if __name__ == "__main__":
    # Run the test
    document_path = asyncio.run(test_content_generation())

    if document_path:
        print(f"\nTest completed successfully. Document saved to: {document_path}")
    else:
        print("\nTest failed. See logs for details.")
