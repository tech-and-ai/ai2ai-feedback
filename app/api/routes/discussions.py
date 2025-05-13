"""
Discussion API routes.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime
import json

from app.db.base import get_db
from app.api.models import (
    SessionCreate, SessionUpdate, MessageCreate,
    SessionResponse, SessionDetailResponse, SessionListResponse,
    MessageResponse, MessageListResponse
)
from app.services.discussion_service import DiscussionService

router = APIRouter()

@router.post("", response_model=SessionResponse, status_code=201)
async def create_discussion(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new discussion session.
    """
    discussion_service = DiscussionService(db)
    session = await discussion_service.create_session(
        session_data.title,
        session_data.system_prompt,
        session_data.tags
    )
    return session

@router.get("", response_model=SessionListResponse)
async def list_discussions(
    status: Optional[str] = None,
    tag: Optional[str] = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    List discussion sessions with optional filtering.
    """
    discussion_service = DiscussionService(db)
    sessions, total = await discussion_service.list_sessions(status, tag, limit, offset)
    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "sessions": sessions
    }

@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_discussion(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific discussion session.
    """
    discussion_service = DiscussionService(db)
    session = await discussion_service.get_session_with_messages(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Discussion session not found")
    return session

@router.put("/{session_id}", response_model=SessionResponse)
async def update_discussion(
    session_id: str,
    session_data: SessionUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update a discussion session.
    """
    discussion_service = DiscussionService(db)
    session = await discussion_service.update_session(session_id, session_data)
    if not session:
        raise HTTPException(status_code=404, detail="Discussion session not found")
    return session

@router.post("/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    message_data: MessageCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message in a discussion.
    """
    discussion_service = DiscussionService(db)
    message = await discussion_service.add_message(
        session_id,
        message_data.role,
        message_data.content,
        message_data.metadata
    )
    if not message:
        raise HTTPException(status_code=404, detail="Discussion session not found")
    
    # If the message is from a user, generate a response in the background
    if message_data.role == "user":
        background_tasks.add_task(
            discussion_service.generate_response,
            session_id,
            message.id
        )
    
    return message

@router.get("/{session_id}/messages", response_model=MessageListResponse)
async def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=100),
    before: Optional[datetime] = None,
    after: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Get messages from a discussion.
    """
    discussion_service = DiscussionService(db)
    messages = await discussion_service.get_messages(session_id, limit, before, after)
    if messages is None:
        raise HTTPException(status_code=404, detail="Discussion session not found")
    return {"session_id": session_id, "messages": messages}

@router.get("/{session_id}/stream")
async def stream_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream messages from a discussion in real-time.
    """
    discussion_service = DiscussionService(db)
    
    # Check if session exists
    session = await discussion_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Discussion session not found")
    
    async def message_generator():
        # Send initial event with session info
        yield f"data: {json.dumps({'type': 'session_info', 'session_id': session_id})}\n\n"
        
        # Stream messages
        async for message in discussion_service.stream_messages(session_id):
            yield f"data: {json.dumps({'type': 'message', 'content': message})}\n\n"
    
    return StreamingResponse(
        message_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable buffering in Nginx
        }
    )
