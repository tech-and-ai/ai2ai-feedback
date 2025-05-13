"""
Discussion Thread

This module provides functionality for managing discussion threads.
"""

import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.discussion import Discussion, DiscussionStatus
from models.message import Message

logger = logging.getLogger(__name__)

class DiscussionThread:
    """Discussion thread class."""
    
    def __init__(self, db_connection, discussion_id: Optional[str] = None):
        """
        Initialize the discussion thread.
        
        Args:
            db_connection: Database connection
            discussion_id: Optional discussion ID
        """
        self.db = db_connection
        self.discussion_id = discussion_id
        self.discussion = None
        logger.info(f"Initialized discussion thread with ID: {discussion_id}")
    
    async def load(self) -> bool:
        """
        Load the discussion.
        
        Returns:
            True if the discussion was loaded, False otherwise
        """
        if not self.discussion_id:
            logger.warning("No discussion ID provided")
            return False
        
        # Load discussion from database
        self.discussion = await self.db.discussions.get(self.discussion_id)
        
        if not self.discussion:
            logger.warning(f"Discussion not found: {self.discussion_id}")
            return False
        
        logger.info(f"Loaded discussion: {self.discussion_id}")
        return True
    
    async def create(self, task_id: str, title: str, metadata: Optional[Dict[str, Any]] = None) -> Discussion:
        """
        Create a new discussion.
        
        Args:
            task_id: Task ID
            title: Discussion title
            metadata: Optional metadata
            
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
            metadata=metadata or {}
        )
        
        # Save discussion to database
        await self.db.discussions.create(discussion)
        
        self.discussion_id = discussion_id
        self.discussion = discussion
        
        logger.info(f"Created discussion {discussion_id}: {title}")
        return discussion
    
    async def add_message(self, 
                         agent_id: str, 
                         content: str, 
                         parent_message_id: Optional[str] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> Message:
        """
        Add a message to the discussion.
        
        Args:
            agent_id: Agent ID
            content: Message content
            parent_message_id: Optional parent message ID
            metadata: Optional metadata
            
        Returns:
            Created message
        """
        if not self.discussion:
            if not await self.load():
                raise ValueError("Discussion not loaded")
        
        message_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        message = Message(
            id=message_id,
            discussion_id=self.discussion_id,
            agent_id=agent_id,
            content=content,
            created_at=now,
            parent_message_id=parent_message_id,
            metadata=metadata or {}
        )
        
        # Save message to database
        await self.db.messages.create(message)
        
        # Update discussion
        await self.db.discussions.update(self.discussion_id, updated_at=now)
        
        logger.info(f"Added message {message_id} to discussion {self.discussion_id}")
        return message
    
    async def get_messages(self, 
                          agent_id: Optional[str] = None,
                          parent_message_id: Optional[str] = None,
                          limit: int = 100,
                          offset: int = 0) -> List[Message]:
        """
        Get messages in the discussion.
        
        Args:
            agent_id: Optional agent ID filter
            parent_message_id: Optional parent message ID filter
            limit: Maximum number of messages to return
            offset: Offset for pagination
            
        Returns:
            List of messages
        """
        if not self.discussion:
            if not await self.load():
                raise ValueError("Discussion not loaded")
        
        filters = {'discussion_id': self.discussion_id}
        
        if agent_id:
            filters['agent_id'] = agent_id
        
        if parent_message_id:
            filters['parent_message_id'] = parent_message_id
        
        messages = await self.db.messages.list(filters, limit, offset)
        return messages
    
    async def update_status(self, status: DiscussionStatus) -> Discussion:
        """
        Update the discussion status.
        
        Args:
            status: New status
            
        Returns:
            Updated discussion
        """
        if not self.discussion:
            if not await self.load():
                raise ValueError("Discussion not loaded")
        
        now = datetime.utcnow().isoformat()
        
        # Update discussion
        self.discussion = await self.db.discussions.update(
            self.discussion_id,
            status=status,
            updated_at=now
        )
        
        logger.info(f"Updated discussion {self.discussion_id} status to {status}")
        return self.discussion
