#!/usr/bin/env python3
"""
Test Landing Page Generation

This script tests the AI2AI Feedback System by generating a landing page.
"""

import os
import sys
import asyncio
import logging
import json
import sqlite3
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import core components
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.output_processor import OutputProcessor
from models.agent import Agent, AgentStatus
from models.task import Task, TaskStatus, TaskPriority
from models.output import Output, OutputType
from utils.config import load_config

async def generate_landing_page():
    """Generate a landing page using the AI2AI Feedback System."""
    # Load configuration
    config = load_config('default')

    # Initialize model router
    model_router = ModelRouter(config.model_providers)

    # Initialize prompt manager
    prompt_manager = PromptManager(config.prompt_templates)

    # Initialize output processor
    class MockDB:
        """Mock database connection for testing."""

        class MockOutputs:
            """Mock outputs repository."""

            async def create(self, output):
                """Create an output."""
                logger.info(f"Created output: {output.id}")
                return output

        def __init__(self):
            """Initialize the mock database."""
            self.outputs = self.MockOutputs()

    output_processor = OutputProcessor(MockDB())

    # Create a task
    task = Task(
        id="test_landing_page",
        title="Generate Landing Page",
        description="Create a responsive HTML landing page for a SaaS product with modern design and animations.",
        status=TaskStatus.NOT_STARTED,
        priority=TaskPriority.HIGH,
        created_at=datetime.now().isoformat(),
        updated_at=datetime.now().isoformat(),
        assigned_agent_id="agent2",
        parent_task_id=None,
        metadata={
            "expected_output_format": "html",
            "include_css": True,
            "include_javascript": True
        }
    )

    # Create an agent
    agent = Agent(
        id="agent2",
        name="DeepSeek Coder",
        description="Code-focused agent using DeepSeek Coder model",
        model="deepseek-coder-v2:16b",
        capabilities={
            "code_generation": True,
            "code_explanation": True,
            "code_review": True
        },
        status=AgentStatus.AVAILABLE,
        last_active=datetime.now().isoformat(),
        configuration={}
    )

    # Generate system prompt
    system_prompt = """You are an expert web developer with extensive experience in creating modern, responsive, and interactive websites. You excel at writing clean, well-structured HTML, CSS, and JavaScript code that follows best practices and is fully functional without requiring any backend."""

    # Generate execution prompt
    execution_prompt = """
    # Task Execution

    ## Task Details
    - Title: Generate Landing Page
    - Description: Create a responsive HTML landing page for a SaaS product with modern design and animations.

    ## Instructions
    Based on the task details, create a complete HTML landing page with CSS and JavaScript.

    Follow these guidelines:
    1. Generate actual HTML, CSS, and JavaScript code, not just descriptions or explanations
    2. The output should be fully functional code that can be directly used in a web page
    3. Include the following sections:
       - Hero section with animated headline and call-to-action button
       - Features section highlighting 4-6 product features with icons
       - Pricing section with at least 3 pricing tiers
       - Testimonials section with 2-3 customer testimonials
       - Contact form section
       - Footer with contact information and social media links
    4. Incorporate animations using JavaScript (fade-ins, parallax effects, hover animations, etc.)
    5. Ensure the page is responsive and works on mobile and desktop
    6. Include comments in the code explaining key components
    7. Use modern HTML5, CSS3, and ES6+ JavaScript features

    ## Output Format
    The primary output should be complete HTML code with embedded CSS and JavaScript:
    - Start with <!DOCTYPE html> and include all necessary HTML structure
    - Include CSS in a <style> tag in the head section
    - Include JavaScript in a <script> tag at the end of the body section
    - Make sure all code is properly formatted and indented
    - Include comments explaining key components and functionality
    - The code should be fully functional without requiring any backend
    """

    # Use model to generate landing page
    try:
        logger.info("Generating landing page...")

        # Use DeepSeek Coder model with the correct configuration
        landing_page = await model_router.route_request(
            prompt=execution_prompt,
            agent=agent,
            system_prompt=system_prompt,
            max_tokens=8000,
            temperature=0.7,
            top_p=0.95
        )

        # Process and validate output
        output = await output_processor.process_output(
            task=task,
            agent=agent,
            content=landing_page,
            output_type=OutputType.HTML,
            metadata={"generated_by": agent.model}
        )

        # Save landing page to file
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)

        file_path = os.path.join(output_dir, "landing_page.html")
        with open(file_path, "w") as f:
            f.write(landing_page)

        logger.info(f"Landing page saved to: {file_path}")

        return file_path, landing_page
    except Exception as e:
        logger.error(f"Error generating landing page: {e}")
        raise

if __name__ == "__main__":
    # Run the async function
    file_path, landing_page = asyncio.run(generate_landing_page())

    # Print the first 500 characters of the landing page
    print("\nLanding Page Preview (first 500 characters):")
    print("-" * 80)
    print(landing_page[:500])
    print("-" * 80)
    print(f"\nFull landing page saved to: {file_path}")
