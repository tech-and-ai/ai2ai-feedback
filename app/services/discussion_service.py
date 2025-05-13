"""
Discussion service module.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, and_
from typing import List, Optional, Tuple, Dict, Any, AsyncGenerator
from datetime import datetime
import uuid
import json
import asyncio

from app.db.models import Session, Message
from app.api.models import SessionUpdate

class DiscussionService:
    """
    Service for discussion management.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_session(
        self,
        title: str,
        system_prompt: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Session:
        """
        Create a new discussion session.
        """
        # Create session
        session = Session(
            id=str(uuid.uuid4()),
            title=title,
            system_prompt=system_prompt,
            tags=json.dumps(tags) if tags else None,
            status="active"
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        # Add system message if system prompt is provided
        if system_prompt:
            await self.add_message(session.id, "system", system_prompt)

        return session

    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get a session by ID.
        """
        query = select(Session).where(Session.id == session_id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_session_with_messages(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session with its messages.
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        # Get messages
        query = select(Message).where(Message.session_id == session_id).order_by(Message.timestamp)
        result = await self.db.execute(query)
        messages = result.scalars().all()

        # Convert to dict
        session_dict = {
            "id": session.id,
            "title": session.title,
            "system_prompt": session.system_prompt,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "status": session.status,
            "tags": json.loads(session.tags) if session.tags else None,
            "messages": messages
        }

        return session_dict

    async def list_sessions(
        self,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> Tuple[List[Session], int]:
        """
        List sessions with optional filtering.
        """
        # Build query
        query = select(Session)
        count_query = select(func.count()).select_from(Session)

        # Apply filters
        if status:
            query = query.where(Session.status == status)
            count_query = count_query.where(Session.status == status)

        if tag:
            query = query.where(Session.tags.like(f"%{tag}%"))
            count_query = count_query.where(Session.tags.like(f"%{tag}%"))

        # Apply pagination
        query = query.order_by(Session.created_at.desc()).offset(offset).limit(limit)

        # Execute queries
        result = await self.db.execute(query)
        count_result = await self.db.execute(count_query)

        sessions = result.scalars().all()
        total = count_result.scalar()

        return sessions, total

    async def update_session(self, session_id: str, session_data: SessionUpdate) -> Optional[Session]:
        """
        Update a session.
        """
        session = await self.get_session(session_id)
        if not session:
            return None

        # Update fields
        if session_data.title is not None:
            session.title = session_data.title

        if session_data.system_prompt is not None:
            session.system_prompt = session_data.system_prompt

        if session_data.status is not None:
            session.status = session_data.status

        if session_data.tags is not None:
            session.tags = json.dumps(session_data.tags)

        session.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(session)

        return session

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Message]:
        """
        Add a message to a session.
        """
        # Check if session exists
        session = await self.get_session(session_id)
        if not session:
            return None

        # Create message
        message = Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            message_metadata=json.dumps(metadata) if metadata else None
        )

        self.db.add(message)

        # Update session updated_at
        session.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(message)

        return message

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
        before: Optional[datetime] = None,
        after: Optional[datetime] = None
    ) -> Optional[List[Message]]:
        """
        Get messages from a session.
        """
        # Check if session exists
        session = await self.get_session(session_id)
        if not session:
            return None

        # Build query
        query = select(Message).where(Message.session_id == session_id)

        # Apply filters
        if before:
            query = query.where(Message.timestamp < before)

        if after:
            query = query.where(Message.timestamp > after)

        # Apply pagination
        query = query.order_by(Message.timestamp).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        messages = result.scalars().all()

        return messages

    async def generate_response(self, session_id: str, message_id: str) -> Optional[Message]:
        """
        Generate a response to a message.
        """
        # This is a placeholder for the actual implementation
        # In a real implementation, this would call an AI model to generate a response

        # Check if session exists
        session = await self.get_session(session_id)
        if not session:
            return None

        # Get the message
        message_query = select(Message).where(Message.id == message_id)
        message_result = await self.db.execute(message_query)
        message = message_result.scalars().first()

        if not message:
            return None

        # Simulate AI processing time
        await asyncio.sleep(1)

        # Create response message
        response = await self.add_message(
            session_id,
            "assistant",
            f"This is an automated response to: {message.content}",
            {"generated": True}
        )

        return response

    async def stream_messages(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream messages from a session in real-time.
        """
        # Check if session exists
        session = await self.get_session(session_id)
        if not session:
            return

        # Get the latest message timestamp
        query = select(func.max(Message.timestamp)).where(Message.session_id == session_id)
        result = await self.db.execute(query)
        latest_timestamp = result.scalar() or datetime.min

        # Stream messages
        while True:
            # Get new messages
            query = select(Message).where(
                and_(
                    Message.session_id == session_id,
                    Message.timestamp > latest_timestamp
                )
            ).order_by(Message.timestamp)

            result = await self.db.execute(query)
            messages = result.scalars().all()

            # Update latest timestamp
            if messages:
                latest_timestamp = messages[-1].timestamp

                # Yield messages
                for message in messages:
                    yield {
                        "id": message.id,
                        "role": message.role,
                        "content": message.content,
                        "timestamp": message.timestamp.isoformat(),
                        "metadata": json.loads(message.message_metadata) if message.message_metadata else None
                    }

            # Wait before checking for new messages
            await asyncio.sleep(1)
