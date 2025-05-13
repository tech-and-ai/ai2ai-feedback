"""
Database Connection

This module provides functions for connecting to the database.
"""

import logging
import sqlite3
import aiosqlite
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection class."""
    
    def __init__(self, database_url: str):
        """
        Initialize the database connection.
        
        Args:
            database_url: Database URL
        """
        self.database_url = database_url
        self.connection = None
        self.tasks = TaskRepository(self)
        self.agents = AgentRepository(self)
        self.outputs = OutputRepository(self)
        self.discussions = DiscussionRepository(self)
        self.messages = MessageRepository(self)
    
    async def connect(self):
        """Connect to the database."""
        try:
            self.connection = await aiosqlite.connect(self.database_url)
            self.connection.row_factory = sqlite3.Row
            logger.info(f"Connected to database: {self.database_url}")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise
    
    async def close(self):
        """Close the database connection."""
        if self.connection:
            await self.connection.close()
            logger.info("Closed database connection")
    
    async def execute(self, query: str, params: tuple = ()):
        """
        Execute a query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Query result
        """
        if not self.connection:
            await self.connect()
        
        try:
            cursor = await self.connection.execute(query, params)
            await self.connection.commit()
            return cursor
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    async def fetch_one(self, query: str, params: tuple = ()):
        """
        Fetch a single row.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Single row
        """
        if not self.connection:
            await self.connect()
        
        try:
            cursor = await self.connection.execute(query, params)
            row = await cursor.fetchone()
            return row
        except Exception as e:
            logger.error(f"Error fetching row: {e}")
            raise
    
    async def fetch_all(self, query: str, params: tuple = ()):
        """
        Fetch all rows.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            All rows
        """
        if not self.connection:
            await self.connect()
        
        try:
            cursor = await self.connection.execute(query, params)
            rows = await cursor.fetchall()
            return rows
        except Exception as e:
            logger.error(f"Error fetching rows: {e}")
            raise

class BaseRepository:
    """Base repository class."""
    
    def __init__(self, db: DatabaseConnection):
        """
        Initialize the repository.
        
        Args:
            db: Database connection
        """
        self.db = db

class TaskRepository(BaseRepository):
    """Task repository class."""
    
    async def create(self, task):
        """
        Create a task.
        
        Args:
            task: Task to create
            
        Returns:
            Created task
        """
        query = """
        INSERT INTO tasks (
            id, title, description, status, priority, created_at, updated_at,
            assigned_agent_id, parent_task_id, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            task.id, task.title, task.description, task.status, task.priority,
            task.created_at, task.updated_at, task.assigned_agent_id,
            task.parent_task_id, task.metadata
        )
        
        await self.db.execute(query, params)
        return task
    
    async def get(self, task_id: str):
        """
        Get a task by ID.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task if found, None otherwise
        """
        query = "SELECT * FROM tasks WHERE id = ?"
        row = await self.db.fetch_one(query, (task_id,))
        
        if row:
            return row
        
        return None
    
    async def update(self, task_id: str, **kwargs):
        """
        Update a task.
        
        Args:
            task_id: Task ID
            **kwargs: Fields to update
            
        Returns:
            Updated task if found, None otherwise
        """
        # Build update query
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE tasks SET {set_clause} WHERE id = ?"
        
        # Build parameters
        params = tuple(kwargs.values()) + (task_id,)
        
        await self.db.execute(query, params)
        
        # Get updated task
        return await self.get(task_id)
    
    async def delete(self, task_id: str):
        """
        Delete a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task was deleted, False otherwise
        """
        query = "DELETE FROM tasks WHERE id = ?"
        cursor = await self.db.execute(query, (task_id,))
        
        return cursor.rowcount > 0
    
    async def list(self, filters=None, limit=100, offset=0, order_by=None):
        """
        List tasks with optional filtering.
        
        Args:
            filters: Optional filters
            limit: Maximum number of tasks to return
            offset: Offset for pagination
            order_by: Optional ordering
            
        Returns:
            List of tasks
        """
        query = "SELECT * FROM tasks"
        params = []
        
        # Add filters
        if filters:
            filter_clauses = []
            
            for key, value in filters.items():
                filter_clauses.append(f"{key} = ?")
                params.append(value)
            
            if filter_clauses:
                query += " WHERE " + " AND ".join(filter_clauses)
        
        # Add ordering
        if order_by:
            order_clauses = []
            
            for field, direction in order_by:
                order_clauses.append(f"{field} {direction}")
            
            if order_clauses:
                query += " ORDER BY " + ", ".join(order_clauses)
        
        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = await self.db.fetch_all(query, tuple(params))
        return rows

class AgentRepository(BaseRepository):
    """Agent repository class."""
    
    async def create(self, agent):
        """Create an agent."""
        query = """
        INSERT INTO agents (
            id, name, description, model, capabilities, status, last_active, configuration
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            agent.id, agent.name, agent.description, agent.model,
            agent.capabilities, agent.status, agent.last_active, agent.configuration
        )
        
        await self.db.execute(query, params)
        return agent
    
    async def get(self, agent_id: str):
        """Get an agent by ID."""
        query = "SELECT * FROM agents WHERE id = ?"
        row = await self.db.fetch_one(query, (agent_id,))
        
        if row:
            return row
        
        return None
    
    async def update(self, agent_id: str, **kwargs):
        """Update an agent."""
        # Build update query
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        query = f"UPDATE agents SET {set_clause} WHERE id = ?"
        
        # Build parameters
        params = tuple(kwargs.values()) + (agent_id,)
        
        await self.db.execute(query, params)
        
        # Get updated agent
        return await self.get(agent_id)
    
    async def delete(self, agent_id: str):
        """Delete an agent."""
        query = "DELETE FROM agents WHERE id = ?"
        cursor = await self.db.execute(query, (agent_id,))
        
        return cursor.rowcount > 0
    
    async def list(self, filters=None, limit=100, offset=0):
        """List agents with optional filtering."""
        query = "SELECT * FROM agents"
        params = []
        
        # Add filters
        if filters:
            filter_clauses = []
            
            for key, value in filters.items():
                filter_clauses.append(f"{key} = ?")
                params.append(value)
            
            if filter_clauses:
                query += " WHERE " + " AND ".join(filter_clauses)
        
        # Add limit and offset
        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = await self.db.fetch_all(query, tuple(params))
        return rows

class OutputRepository(BaseRepository):
    """Output repository class."""
    
    async def create(self, output):
        """Create an output."""
        query = """
        INSERT INTO outputs (
            id, task_id, agent_id, type, content, created_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            output.id, output.task_id, output.agent_id, output.type,
            output.content, output.created_at, output.metadata
        )
        
        await self.db.execute(query, params)
        return output

class DiscussionRepository(BaseRepository):
    """Discussion repository class."""
    
    async def create(self, discussion):
        """Create a discussion."""
        query = """
        INSERT INTO discussions (
            id, task_id, title, status, created_at, updated_at, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            discussion.id, discussion.task_id, discussion.title, discussion.status,
            discussion.created_at, discussion.updated_at, discussion.metadata
        )
        
        await self.db.execute(query, params)
        return discussion

class MessageRepository(BaseRepository):
    """Message repository class."""
    
    async def create(self, message):
        """Create a message."""
        query = """
        INSERT INTO messages (
            id, discussion_id, agent_id, content, created_at, parent_message_id, metadata
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            message.id, message.discussion_id, message.agent_id, message.content,
            message.created_at, message.parent_message_id, message.metadata
        )
        
        await self.db.execute(query, params)
        return message

def get_db_connection(database_url: str) -> DatabaseConnection:
    """
    Get a database connection.
    
    Args:
        database_url: Database URL
        
    Returns:
        Database connection
    """
    return DatabaseConnection(database_url)
