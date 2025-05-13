#!/usr/bin/env python3
"""
Test script for the AI2AI Feedback Discussion API with DeepSeek Coder

This script demonstrates how to use the AI2AI Feedback Discussion API
with the DeepSeek Coder model for collaborative problem-solving.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import core components
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from models.agent import Agent, AgentStatus
from models.discussion import Discussion, DiscussionStatus
from models.message import Message
from utils.config import load_config

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

        async def list(self, filters=None, limit=100, offset=0, order_by=None):
            """List items with optional filtering."""
            items = list(self.items.values())

            if filters:
                for key, value in filters.items():
                    items = [item for item in items if getattr(item, key, None) == value]

            return items[offset:offset+limit]

    def __init__(self):
        """Initialize the mock database."""
        self.discussions = self.MockRepository("discussion")
        self.messages = self.MockRepository("message")

    async def connect(self):
        """Connect to the database."""
        logger.info("Connected to mock database")

    async def close(self):
        """Close the database connection."""
        logger.info("Closed mock database connection")

class DiscussionAPI:
    """Discussion API for AI2AI Feedback."""

    def __init__(self, model_router, prompt_manager, db):
        """
        Initialize the Discussion API.

        Args:
            model_router: Model router
            prompt_manager: Prompt manager
            db: Database connection
        """
        self.model_router = model_router
        self.prompt_manager = prompt_manager
        self.db = db
        logger.info("Discussion API initialized")

    async def create_discussion(self, title: str, task_id: str) -> Discussion:
        """
        Create a new discussion.

        Args:
            title: Discussion title
            task_id: Task ID

        Returns:
            Created discussion
        """
        discussion_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        discussion = Discussion(
            id=discussion_id,
            task_id=task_id,
            title=title,
            status=DiscussionStatus.ACTIVE,
            created_at=now,
            updated_at=now,
            metadata={}
        )

        # Save discussion to database
        await self.db.discussions.create(discussion)

        logger.info(f"Created discussion {discussion_id}: {title}")
        return discussion

    async def add_message(self,
                         discussion_id: str,
                         agent_id: str,
                         content: str,
                         parent_message_id: Optional[str] = None) -> Message:
        """
        Add a message to a discussion.

        Args:
            discussion_id: Discussion ID
            agent_id: Agent ID
            content: Message content
            parent_message_id: Optional parent message ID

        Returns:
            Created message
        """
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        message = Message(
            id=message_id,
            discussion_id=discussion_id,
            agent_id=agent_id,
            content=content,
            created_at=now,
            parent_message_id=parent_message_id,
            metadata={}
        )

        # Save message to database
        await self.db.messages.create(message)

        # Update discussion
        discussion = await self.db.discussions.get(discussion_id)
        if discussion:
            await self.db.discussions.update(discussion_id, updated_at=now)

        logger.info(f"Added message {message_id} to discussion {discussion_id}")
        return message

    async def get_messages(self, discussion_id: str) -> List[Message]:
        """
        Get messages in a discussion.

        Args:
            discussion_id: Discussion ID

        Returns:
            List of messages
        """
        messages = await self.db.messages.list(
            filters={'discussion_id': discussion_id},
            order_by=[('created_at', 'asc')]
        )

        return messages

    async def generate_response(self,
                              discussion_id: str,
                              agent: Agent,
                              system_prompt: Optional[str] = None) -> Message:
        """
        Generate a response in a discussion.

        Args:
            discussion_id: Discussion ID
            agent: Agent to generate the response
            system_prompt: Optional system prompt

        Returns:
            Generated message
        """
        # Get messages in the discussion
        messages = await self.get_messages(discussion_id)

        if not messages:
            logger.warning(f"No messages found in discussion {discussion_id}")
            return None

        # Format messages for the model
        formatted_messages = self._format_messages(messages)

        # Create prompt for the model
        prompt = f"""
        You are participating in a discussion with other AI agents. Please provide a helpful response
        based on the conversation history below. Respond in English.

        Discussion History:
        {formatted_messages}

        Your response:
        """

        # Use model to generate response
        try:
            logger.info(f"Generating response with model {agent.model}")

            response = await self.model_router.route_request(
                prompt=prompt,
                agent=agent,
                system_prompt=system_prompt or "You are a helpful AI assistant participating in a collaborative discussion. Always respond in English.",
                max_tokens=1000,
                temperature=0.7,
                top_p=0.95
            )

            # Add response to discussion
            message = await self.add_message(
                discussion_id=discussion_id,
                agent_id=agent.id,
                content=response,
                parent_message_id=messages[-1].id if messages else None
            )

            return message
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return None

    def _format_messages(self, messages: List[Message]) -> str:
        """
        Format messages for the model.

        Args:
            messages: List of messages

        Returns:
            Formatted messages
        """
        formatted = []

        for message in messages:
            formatted.append(f"Agent {message.agent_id}: {message.content}")

        return "\n\n".join(formatted)

async def main():
    """Main function."""
    # Load configuration
    config = load_config('default')

    # Initialize model router
    model_router = ModelRouter(config.model_providers)

    # Initialize prompt manager
    prompt_manager = PromptManager(config.prompt_templates)

    # Initialize mock database
    db = MockDB()
    await db.connect()

    try:
        # Initialize discussion API
        discussion_api = DiscussionAPI(model_router, prompt_manager, db)

        # Create agents
        agent1 = Agent(
            id="agent1",
            name="DeepSeek Coder",
            description="Code-focused agent using DeepSeek Coder model",
            model="deepseek-coder-v2:16b",
            capabilities={
                "code_generation": True,
                "code_explanation": True,
                "code_review": True
            },
            status=AgentStatus.AVAILABLE,
            last_active=datetime.utcnow().isoformat(),
            configuration={}
        )

        agent2 = Agent(
            id="agent2",
            name="Human",
            description="Human participant",
            model="human",
            capabilities={},
            status=AgentStatus.AVAILABLE,
            last_active=datetime.utcnow().isoformat(),
            configuration={}
        )

        # Create a discussion
        discussion = await discussion_api.create_discussion(
            title="Code Optimization Discussion",
            task_id="code_optimization"
        )

        # Add initial message from human
        initial_message = await discussion_api.add_message(
            discussion_id=discussion.id,
            agent_id=agent2.id,
            content="I have a recursive Fibonacci function in Python that's very slow for large inputs. How can I optimize it?"
        )

        # Generate response from DeepSeek Coder
        response = await discussion_api.generate_response(
            discussion_id=discussion.id,
            agent=agent1,
            system_prompt="You are DeepSeek Coder, an expert in code optimization and best practices. Provide detailed, practical advice for improving code performance and quality."
        )

        # Print the discussion
        messages = await discussion_api.get_messages(discussion.id)

        print("\nDiscussion:")
        print("-" * 80)
        for message in messages:
            print(f"Agent {message.agent_id}: {message.content}")
            print("-" * 80)

        # Add follow-up question
        follow_up = await discussion_api.add_message(
            discussion_id=discussion.id,
            agent_id=agent2.id,
            content="Can you provide a specific implementation using memoization?"
        )

        # Generate another response
        response2 = await discussion_api.generate_response(
            discussion_id=discussion.id,
            agent=agent1
        )

        # Print the updated discussion
        messages = await discussion_api.get_messages(discussion.id)

        print("\nUpdated Discussion:")
        print("-" * 80)
        for message in messages:
            print(f"Agent {message.agent_id}: {message.content}")
            print("-" * 80)

    finally:
        # Close database connection
        await db.close()

if __name__ == "__main__":
    # Run the async function
    asyncio.run(main())
