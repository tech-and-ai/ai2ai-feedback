"""
Controller Agent Initialization

This module initializes the controller agent on application startup.
"""

import logging
import uuid
import asyncio
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from .database import Agent, async_session
from .controller_agent import ControllerAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("controller-init")

# Global controller agent instance
controller_instance: Optional[ControllerAgent] = None

async def get_or_create_controller_agent(db: AsyncSession) -> Agent:
    """
    Get or create a controller agent

    Args:
        db: Database session

    Returns:
        Agent: Controller agent
    """
    # Check if controller agent exists
    query = select(Agent).where(
        Agent.agent_type == "controller"
    )
    result = await db.execute(query)
    controller = result.scalars().first()

    if controller:
        logger.info(f"Found existing controller agent: {controller.name} ({controller.agent_id})")
        return controller

    # Create a unique agent ID
    agent_id = str(uuid.uuid4())

    # Create controller agent
    controller = Agent(
        agent_id=agent_id,
        session_id="controller_session",
        agent_index=0,
        name="Project Controller",
        role="Project Manager",
        skills="planning,coordination,management",  # Comma-separated string
        model="gemma3:4b",
        status="idle",
        agent_type="controller",
        current_workload=0,
        max_workload=10
    )
    db.add(controller)
    await db.commit()

    logger.info(f"Created new controller agent: {controller.name} ({controller.agent_id})")
    return controller

async def start_controller_agent():
    """
    Start the controller agent

    Returns:
        bool: True if successful, False otherwise
    """
    global controller_instance

    try:
        # Get database session
        async with async_session() as db:
            # Get or create controller agent
            controller = await get_or_create_controller_agent(db)

            # Get endpoint from performance_metrics if available
            endpoint = None
            try:
                if controller.performance_metrics:
                    performance_metrics = json.loads(controller.performance_metrics)
                    endpoint = performance_metrics.get("endpoint")
            except:
                logger.warning(f"Failed to parse performance_metrics for controller {controller.name}")

            # Create controller agent instance
            controller_instance = ControllerAgent(
                controller.agent_id,
                controller.name,
                controller.role,
                controller.model,
                endpoint
            )

            # Start controller agent
            await controller_instance.start()

            # Update agent status
            controller.status = "running"
            await db.commit()

            logger.info(f"Controller agent started: {controller.name} ({controller.agent_id})")
            return True
    except Exception as e:
        logger.error(f"Error starting controller agent: {e}")
        return False

async def stop_controller_agent():
    """
    Stop the controller agent

    Returns:
        bool: True if successful, False otherwise
    """
    global controller_instance

    try:
        if controller_instance:
            # Stop controller agent
            await controller_instance.stop()

            # Update agent status
            async with async_session() as db:
                query = select(Agent).where(
                    Agent.agent_id == controller_instance.agent_id
                )
                result = await db.execute(query)
                controller = result.scalars().first()

                if controller:
                    controller.status = "idle"
                    await db.commit()

            controller_instance = None
            logger.info("Controller agent stopped")
            return True
        else:
            logger.warning("No controller agent to stop")
            return False
    except Exception as e:
        logger.error(f"Error stopping controller agent: {e}")
        return False
