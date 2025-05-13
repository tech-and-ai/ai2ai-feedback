#!/usr/bin/env python3
"""
Test System

This script tests the core components of the AI2AI Feedback System.
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
from core.task_manager import TaskManager
from core.agent_manager import AgentManager
from core.output_processor import OutputProcessor
from models.agent import Agent, AgentStatus
from models.task import Task, TaskStatus, TaskPriority
from models.output import Output, OutputType

class MockDB:
    """Mock database connection for testing."""
    
    class MockRepository:
        """Mock repository."""
        
        def __init__(self, name):
            """Initialize the mock repository."""
            self.name = name
            self.items = {}
        
        async def create(self, item):
            """Create an item."""
            self.items[item.id] = item
            logger.info(f"Created {self.name}: {item.id}")
            return item
        
        async def get(self, item_id):
            """Get an item by ID."""
            return self.items.get(item_id)
        
        async def update(self, item_id, **kwargs):
            """Update an item."""
            item = self.items.get(item_id)
            if item:
                for key, value in kwargs.items():
                    setattr(item, key, value)
                logger.info(f"Updated {self.name}: {item_id}")
            return item
        
        async def delete(self, item_id):
            """Delete an item."""
            if item_id in self.items:
                del self.items[item_id]
                logger.info(f"Deleted {self.name}: {item_id}")
                return True
            return False
        
        async def list(self, filters=None, limit=100, offset=0, order_by=None):
            """List items with optional filtering."""
            items = list(self.items.values())
            
            if filters:
                for key, value in filters.items():
                    items = [item for item in items if getattr(item, key, None) == value]
            
            return items[offset:offset+limit]
    
    def __init__(self):
        """Initialize the mock database."""
        self.tasks = self.MockRepository("task")
        self.agents = self.MockRepository("agent")
        self.outputs = self.MockRepository("output")
        self.discussions = self.MockRepository("discussion")
        self.messages = self.MockRepository("message")
    
    async def connect(self):
        """Connect to the database."""
        logger.info("Connected to mock database")
    
    async def close(self):
        """Close the database connection."""
        logger.info("Closed mock database connection")

async def test_system():
    """Test the core components of the AI2AI Feedback System."""
    # Initialize mock database
    db = MockDB()
    await db.connect()
    
    try:
        # Initialize core components
        task_manager = TaskManager(db)
        agent_manager = AgentManager(db)
        output_processor = OutputProcessor(db)
        
        logger.info("Initialized core components")
        
        # Create an agent
        agent = await agent_manager.create_agent(
            name="Test Agent",
            description="Agent for testing",
            model="test-model",
            capabilities={"testing": True},
            configuration={}
        )
        
        logger.info(f"Created agent: {agent.id}")
        
        # Create a task
        task = await task_manager.create_task(
            title="Test Task",
            description="Task for testing",
            priority=TaskPriority.MEDIUM,
            assigned_agent_id=agent.id
        )
        
        logger.info(f"Created task: {task.id}")
        
        # Update agent status
        agent = await agent_manager.update_agent_status(agent.id, AgentStatus.BUSY)
        
        logger.info(f"Updated agent status: {agent.status}")
        
        # Update task status
        task = await task_manager.update_task_status(task.id, TaskStatus.PLANNING)
        
        logger.info(f"Updated task status: {task.status}")
        
        # Create a sample HTML landing page
        landing_page = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SaaS Landing Page</title>
    <style>
        /* Reset and base styles */
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        
        .container {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }
        
        /* Hero section */
        .hero {
            background: linear-gradient(135deg, #4a6cf7 0%, #24bddf 100%);
            color: white;
            padding: 100px 0;
            text-align: center;
        }
        
        .hero h1 {
            font-size: 48px;
            margin-bottom: 20px;
            animation: fadeIn 1s ease-in-out;
        }
        
        .hero p {
            font-size: 20px;
            margin-bottom: 30px;
            animation: fadeIn 1s ease-in-out 0.3s forwards;
            opacity: 0;
        }
        
        .btn {
            display: inline-block;
            background-color: white;
            color: #4a6cf7;
            padding: 12px 30px;
            border-radius: 30px;
            text-decoration: none;
            font-weight: bold;
            transition: all 0.3s ease;
            animation: fadeIn 1s ease-in-out 0.6s forwards;
            opacity: 0;
        }
        
        .btn:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        /* Animations */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <section class="hero">
        <div class="container">
            <h1>Welcome to Our SaaS Platform</h1>
            <p>The all-in-one solution for your business needs</p>
            <a href="#" class="btn">Get Started</a>
        </div>
    </section>
    
    <script>
        // Simple animation script
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded!');
        });
    </script>
</body>
</html>"""
        
        # Process and validate output
        output = await output_processor.process_output(
            task=task,
            agent=agent,
            content=landing_page,
            output_type=OutputType.HTML,
            metadata={"generated_by": "test"}
        )
        
        logger.info(f"Created output: {output.id}")
        
        # Save landing page to file
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        
        file_path = os.path.join(output_dir, "test_landing_page.html")
        with open(file_path, "w") as f:
            f.write(landing_page)
        
        logger.info(f"Landing page saved to: {file_path}")
        
        # Update task status to completed
        task = await task_manager.update_task_status(task.id, TaskStatus.COMPLETED)
        
        logger.info(f"Updated task status: {task.status}")
        
        # Update agent status to available
        agent = await agent_manager.update_agent_status(agent.id, AgentStatus.AVAILABLE)
        
        logger.info(f"Updated agent status: {agent.status}")
        
        return file_path, landing_page
    finally:
        # Close database connection
        await db.close()

if __name__ == "__main__":
    # Run the async function
    file_path, landing_page = asyncio.run(test_system())
    
    # Print the first 500 characters of the landing page
    print("\nLanding Page Preview (first 500 characters):")
    print("-" * 80)
    print(landing_page[:500])
    print("-" * 80)
    print(f"\nFull landing page saved to: {file_path}")
    
    # Open the landing page in a browser
    import webbrowser
    webbrowser.open(f"file://{os.path.abspath(file_path)}")
