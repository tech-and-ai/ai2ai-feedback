#!/usr/bin/env python3
"""
Test Workers - Script to test the worker system
"""
import os
import asyncio
from dotenv import load_dotenv
from worker_manager import WorkerManager

# Load environment variables
load_dotenv()

async def test_workers():
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY environment variable not set")
        print("Please set the environment variable and try again")
        return

    # Initialize worker manager
    worker_manager = WorkerManager(api_key)

    print("=== Testing AI Worker System ===")

    # Activate two workers for testing
    print("\nActivating Tool Framework Developer and Stripe Customer Tools Developer...")

    tool_framework_worker = await worker_manager.activate_worker("tool_framework", model="google/gemini-2.5-flash-preview")
    stripe_customer_worker = await worker_manager.activate_worker("stripe_customer", model="google/gemini-2.5-flash-preview")

    print(f"\nActivated workers:")
    print(f"- {tool_framework_worker['name']} (Session ID: {tool_framework_worker['session_id']})")
    print(f"- {stripe_customer_worker['name']} (Session ID: {stripe_customer_worker['session_id']})")

    # Assign tasks to workers
    print("\nAssigning tasks to workers...")

    # Task for Tool Framework Developer
    tool_framework_task = """
    Create a simple Python class called 'Tool' with the following attributes:
    - name (str): The name of the tool
    - description (str): A description of what the tool does
    - execute (method): A method that executes the tool's functionality

    Include proper type hints and docstrings.
    """

    tool_framework_result = await worker_manager.assign_task(
        tool_framework_worker['session_id'],
        tool_framework_task
    )

    # Task for Stripe Customer Tools Developer
    stripe_customer_task = """
    Create a Python function called 'create_customer' that creates a new customer in Stripe.
    The function should:
    - Take parameters for email, name, and optional metadata
    - Use the Stripe Python library
    - Include proper error handling
    - Return the created customer object

    Include proper type hints and docstrings.
    """

    stripe_customer_result = await worker_manager.assign_task(
        stripe_customer_worker['session_id'],
        stripe_customer_task
    )

    # Print results
    print("\n=== Tool Framework Developer Response ===")
    print(tool_framework_result['response'])

    print("\n=== Stripe Customer Tools Developer Response ===")
    print(stripe_customer_result['response'])

    # Deactivate workers
    print("\nDeactivating workers...")
    await worker_manager.deactivate_worker(tool_framework_worker['session_id'])
    await worker_manager.deactivate_worker(stripe_customer_worker['session_id'])

    print("All workers deactivated")
    print("\nTest complete!")

if __name__ == "__main__":
    asyncio.run(test_workers())
