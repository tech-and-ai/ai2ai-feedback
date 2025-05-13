"""
Agent Manager

This module is responsible for managing agent configuration,
availability, and capabilities.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.agent import Agent, AgentStatus

logger = logging.getLogger(__name__)

class AgentManager:
    """
    Agent Manager class for managing agent lifecycle.
    """
    
    def __init__(self, db_connection):
        """
        Initialize the Agent Manager.
        
        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        logger.info("Agent Manager initialized")
    
    async def create_agent(self, 
                          name: str, 
                          description: str, 
                          model: str,
                          capabilities: Optional[Dict[str, Any]] = None,
                          configuration: Optional[Dict[str, Any]] = None) -> Agent:
        """
        Create a new agent.
        
        Args:
            name: Agent name
            description: Agent description
            model: Model identifier
            capabilities: Agent capabilities
            configuration: Agent configuration
            
        Returns:
            Created agent
        """
        agent_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        agent = Agent(
            id=agent_id,
            name=name,
            description=description,
            model=model,
            capabilities=capabilities or {},
            status=AgentStatus.AVAILABLE,
            last_active=now,
            configuration=configuration or {}
        )
        
        # Save agent to database
        await self.db.agents.create(agent)
        
        logger.info(f"Created agent {agent_id}: {name}")
        return agent
    
    async def get_agent(self, agent_id: str) -> Optional[Agent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            Agent if found, None otherwise
        """
        agent = await self.db.agents.get(agent_id)
        return agent
    
    async def update_agent(self, agent_id: str, **kwargs) -> Optional[Agent]:
        """
        Update an agent.
        
        Args:
            agent_id: Agent ID
            **kwargs: Fields to update
            
        Returns:
            Updated agent if found, None otherwise
        """
        # Update agent in database
        agent = await self.db.agents.update(agent_id, **kwargs)
        
        if agent:
            logger.info(f"Updated agent {agent_id}")
        else:
            logger.warning(f"Failed to update agent {agent_id}: not found")
            
        return agent
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: Agent ID
            
        Returns:
            True if agent was deleted, False otherwise
        """
        result = await self.db.agents.delete(agent_id)
        
        if result:
            logger.info(f"Deleted agent {agent_id}")
        else:
            logger.warning(f"Failed to delete agent {agent_id}: not found")
            
        return result
    
    async def list_agents(self, 
                         status: Optional[AgentStatus] = None,
                         model: Optional[str] = None,
                         limit: int = 100,
                         offset: int = 0) -> List[Agent]:
        """
        List agents with optional filtering.
        
        Args:
            status: Filter by status
            model: Filter by model
            limit: Maximum number of agents to return
            offset: Offset for pagination
            
        Returns:
            List of agents
        """
        filters = {}
        
        if status is not None:
            filters['status'] = status
            
        if model is not None:
            filters['model'] = model
            
        agents = await self.db.agents.list(filters, limit, offset)
        return agents
    
    async def update_agent_status(self, agent_id: str, status: AgentStatus) -> Optional[Agent]:
        """
        Update an agent's status.
        
        Args:
            agent_id: Agent ID
            status: New status
            
        Returns:
            Updated agent if found, None otherwise
        """
        now = datetime.utcnow().isoformat()
        return await self.update_agent(agent_id, status=status, last_active=now)
    
    async def get_available_agent(self, capabilities: Optional[Dict[str, Any]] = None) -> Optional[Agent]:
        """
        Get an available agent with optional capability requirements.
        
        Args:
            capabilities: Required capabilities
            
        Returns:
            Available agent if found, None otherwise
        """
        filters = {'status': AgentStatus.AVAILABLE}
        
        agents = await self.db.agents.list(filters)
        
        if not agents:
            return None
        
        # If no capabilities required, return first available agent
        if not capabilities:
            return agents[0]
        
        # Filter agents by capabilities
        for agent in agents:
            if self._has_capabilities(agent, capabilities):
                return agent
        
        return None
    
    def _has_capabilities(self, agent: Agent, required_capabilities: Dict[str, Any]) -> bool:
        """
        Check if an agent has the required capabilities.
        
        Args:
            agent: Agent to check
            required_capabilities: Required capabilities
            
        Returns:
            True if agent has all required capabilities, False otherwise
        """
        for key, value in required_capabilities.items():
            if key not in agent.capabilities:
                return False
            
            if agent.capabilities[key] != value:
                return False
        
        return True
