"""
Tool registry for the AI2AI feedback system.
This module manages the registration and retrieval of tools for agents.
"""

import os
import json
import uuid
import logging
from typing import Dict, Any, List, Optional, Type
from dotenv import load_dotenv

from app.db.models import Tool as ToolModel
from app.tools.agent_tools import (
    FalImageGenerationTool,
    DuckDuckGoSearchTool,
    AI2AIDiscussionTool,
    EmailTool
)

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Tool class registry
TOOL_CLASSES = {
    "fal_image_generation": FalImageGenerationTool,
    "duckduckgo_search": DuckDuckGoSearchTool,
    "ai2ai_discussion": AI2AIDiscussionTool,
    "email": EmailTool
}

class ToolRegistry:
    """Registry for managing agent tools."""
    
    def __init__(self):
        self._tools = {}
        self._initialized = False
    
    def get_tool(self, tool_id: str) -> Optional[Any]:
        """Get a tool instance by ID."""
        return self._tools.get(tool_id)
    
    def get_tool_by_name(self, tool_name: str) -> Optional[Any]:
        """Get a tool instance by name."""
        for tool_id, tool in self._tools.items():
            if tool.__class__.__name__.lower() == tool_name.lower():
                return tool
        return None
    
    def register_tool(self, tool_id: str, tool_instance: Any) -> None:
        """Register a tool instance."""
        self._tools[tool_id] = tool_instance
    
    async def initialize_from_db(self, db_session) -> None:
        """Initialize tools from the database."""
        if self._initialized:
            return
        
        try:
            # Query all tools from the database
            tools = await db_session.query(ToolModel).all()
            
            for tool in tools:
                tool_type = tool.type
                if tool_type in TOOL_CLASSES:
                    # Create an instance of the tool class
                    tool_class = TOOL_CLASSES[tool_type]
                    tool_instance = tool_class()
                    
                    # Register the tool
                    self.register_tool(tool.id, tool_instance)
                    logger.info(f"Registered tool: {tool.name} ({tool.id})")
                else:
                    logger.warning(f"Unknown tool type: {tool_type}")
            
            self._initialized = True
            logger.info(f"Tool registry initialized with {len(self._tools)} tools")
        except Exception as e:
            logger.exception(f"Error initializing tool registry: {str(e)}")
    
    async def register_default_tools(self, db_session) -> None:
        """Register default tools in the database."""
        try:
            # Check if tools already exist
            existing_tools = await db_session.query(ToolModel).all()
            if existing_tools:
                logger.info(f"Default tools already registered ({len(existing_tools)} tools found)")
                return
            
            # Define default tools
            default_tools = [
                {
                    "id": str(uuid.uuid4()),
                    "name": "Image Generation",
                    "description": "Generate images using Fal.ai's API",
                    "type": "fal_image_generation",
                    "config": json.dumps({
                        "default_model": os.getenv("FAL_DEFAULT_MODEL", "fal-ai/flux/dev"),
                        "default_dimensions": [
                            int(os.getenv("FAL_IMAGE_WIDTH", 512)),
                            int(os.getenv("FAL_IMAGE_HEIGHT", 512))
                        ]
                    })
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Web Search",
                    "description": "Search the web using DuckDuckGo",
                    "type": "duckduckgo_search",
                    "config": json.dumps({
                        "default_results": int(os.getenv("DUCKDUCKGO_MAX_RESULTS", 5))
                    })
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "AI Discussion",
                    "description": "Communicate with other AI agents using the discussion API",
                    "type": "ai2ai_discussion",
                    "config": json.dumps({
                        "base_url": os.getenv("AI2AI_API_URL", "http://localhost:8001")
                    })
                },
                {
                    "id": str(uuid.uuid4()),
                    "name": "Email",
                    "description": "Send emails to users or other recipients",
                    "type": "email",
                    "config": json.dumps({
                        "smtp_server": os.getenv("EMAIL_SMTP_SERVER", "smtp.gmail.com"),
                        "smtp_port": int(os.getenv("EMAIL_SMTP_PORT", 587))
                    })
                }
            ]
            
            # Add tools to database
            for tool_data in default_tools:
                tool = ToolModel(**tool_data)
                db_session.add(tool)
            
            await db_session.commit()
            logger.info(f"Registered {len(default_tools)} default tools")
        except Exception as e:
            await db_session.rollback()
            logger.exception(f"Error registering default tools: {str(e)}")

# Global tool registry instance
tool_registry = ToolRegistry()
