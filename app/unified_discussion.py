"""
Unified discussion module for AI-to-AI Feedback API

This module provides a unified approach to discussions between AI agents,
whether one-to-one or one-to-many. It treats the number of agents as a parameter,
with no fundamental difference between feedback and multi-agent discussions.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Set
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Agent, Session, Task, get_db, add_message, add_feedback
from .providers.factory import get_model_provider
from .utils.feedback_parser import extract_structured_feedback, StreamingFeedbackParser
from .task_management import TaskManager, ContextScaffold
from .models import (
    UnifiedDiscussionCreateRequest,
    UnifiedDiscussionMessageRequest,
    UnifiedDiscussionMessageResponse,
    AgentResponse
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/discussion", tags=["Unified Discussion"])

# Store active discussions
active_discussions: Dict[str, Dict] = {}

class DiscussionParticipant:
    """Class representing a participant in a discussion"""

    def __init__(self, agent_id: str, agent_name: str, agent_role: str, agent_model: str):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.agent_model = agent_model
        self.queue = asyncio.Queue()
        self.is_responding = False
        self.last_response_time = None

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "agent_role": self.agent_role,
            "agent_model": self.agent_model,
            "is_responding": self.is_responding,
            "last_response_time": self.last_response_time.isoformat() if self.last_response_time else None
        }

class DiscussionManager:
    """Manager for discussions"""

    def __init__(self, session_id: str, system_prompt: str, chair_role: str = "Claude"):
        self.session_id = session_id
        self.system_prompt = system_prompt
        self.chair_role = chair_role
        self.participants: Dict[str, DiscussionParticipant] = {}
        self.message_history: List[Dict] = []
        self.active_listeners: Set[asyncio.Queue] = set()
        self.lock = asyncio.Lock()

    def add_participant(self, agent_id: str, agent_name: str, agent_role: str, agent_model: str):
        """Add a participant to the discussion"""
        participant = DiscussionParticipant(agent_id, agent_name, agent_role, agent_model)
        self.participants[agent_id] = participant
        return participant

    def get_participant(self, agent_id: str) -> Optional[DiscussionParticipant]:
        """Get a participant by ID"""
        return self.participants.get(agent_id)

    def get_all_participants(self) -> List[DiscussionParticipant]:
        """Get all participants"""
        return list(self.participants.values())

    def add_message(self, sender_id: str, content: str, message_type: str = "response"):
        """Add a message to the discussion history"""
        timestamp = datetime.utcnow()

        # Get sender info
        sender_info = {}
        if sender_id in self.participants:
            participant = self.participants[sender_id]
            sender_info = {
                "agent_id": participant.agent_id,
                "agent_name": participant.agent_name,
                "agent_role": participant.agent_role
            }
        elif sender_id == "user":
            sender_info = {
                "agent_id": "user",
                "agent_name": "User",
                "agent_role": "Human"
            }
        elif sender_id == "chair":
            sender_info = {
                "agent_id": "chair",
                "agent_name": self.chair_role,
                "agent_role": "Discussion Chair"
            }

        # Create message
        message = {
            "id": f"{self.session_id}_{len(self.message_history)}",
            "sender_id": sender_id,
            "sender_info": sender_info,
            "content": content,
            "type": message_type,
            "timestamp": timestamp.isoformat()
        }

        # Add to history
        self.message_history.append(message)

        # Notify listeners
        self._notify_listeners(message)

        return message

    def _notify_listeners(self, message: Dict):
        """Notify all listeners of a new message"""
        for queue in self.active_listeners:
            queue.put_nowait(message)

    def add_listener(self) -> asyncio.Queue:
        """Add a listener to the discussion"""
        queue = asyncio.Queue()
        self.active_listeners.add(queue)
        return queue

    def remove_listener(self, queue: asyncio.Queue):
        """Remove a listener from the discussion"""
        if queue in self.active_listeners:
            self.active_listeners.remove(queue)

    async def get_agent_response(self, agent_id: str, prompt: str, context: Optional[str] = None, question: Optional[str] = None) -> str:
        """Get a response from an agent"""
        participant = self.get_participant(agent_id)
        if not participant:
            raise ValueError(f"Participant {agent_id} not found")

        # Mark as responding
        async with self.lock:
            participant.is_responding = True

        try:
            # Get model provider
            provider = get_model_provider(participant.agent_model)

            # Create system prompt
            if len(self.participants) > 1:
                # Multi-agent discussion prompt
                system_prompt = f"""
{self.system_prompt}

You are {participant.agent_name}, and your role is: {participant.agent_role}

You are participating in a discussion with multiple AI agents. Each agent has a unique perspective and role.
{self.chair_role} acts as the chair of this discussion, orchestrating the conversation.

DISCUSSION GUIDELINES:
1. Directly address other agents by name when responding to their points
2. Ask questions to specific agents based on their expertise
3. Respectfully agree or disagree with other agents' perspectives
4. Build upon ideas proposed by other agents
5. Suggest collaborative approaches that combine multiple viewpoints
6. Feel free to initiate new discussion threads with other agents

Your goal is to create a dynamic, collaborative conversation that feels like a real roundtable discussion.
Keep your response concise (2-3 paragraphs maximum) and focused on adding value.

Discussion history:
{self._format_history_for_prompt()}
"""
            else:
                # One-to-one feedback prompt
                system_prompt = """
You are an expert advisor providing feedback to another AI.
Your goal is to help the other AI improve its reasoning and problem-solving.
Provide clear, specific feedback that addresses the question or challenge presented.
Structure your response as follows:

FEEDBACK_SUMMARY: Brief summary of the key issue or insight

REASONING_ASSESSMENT: Evaluate the reasoning approach, identifying strengths and weaknesses

KNOWLEDGE_GAPS: Identify any missing information or knowledge that would help

SUGGESTED_APPROACH: Provide a clear suggestion for how to proceed

ADDITIONAL_CONSIDERATIONS: Mention any other factors that should be considered
"""

            # Create user prompt
            if len(self.participants) > 1:
                # Multi-agent discussion prompt
                user_prompt = prompt
            else:
                # One-to-one feedback prompt
                user_prompt = f"""
The assistant is working on a problem and has requested feedback. Here is their current reasoning:

{context or prompt}

Specific feedback request: {question or "Please provide feedback on my approach."}
"""

            # Get response
            response = await provider.generate_completion(system_prompt, user_prompt)

            # Update participant
            participant.last_response_time = datetime.utcnow()

            # Add the response to the discussion
            self.add_message(agent_id, response)

            return response
        finally:
            # Mark as not responding
            async with self.lock:
                participant.is_responding = False

    def _format_history_for_prompt(self) -> str:
        """Format message history for inclusion in prompts"""
        formatted = []

        for msg in self.message_history[-10:]:  # Only include last 10 messages
            sender = msg["sender_info"]["agent_name"]
            role = msg["sender_info"]["agent_role"]
            formatted.append(f"{sender} ({role}): {msg['content']}")

        return "\n".join(formatted)

    def to_dict(self):
        """Convert to dictionary representation"""
        return {
            "session_id": self.session_id,
            "participants": [p.to_dict() for p in self.participants.values()],
            "message_count": len(self.message_history),
            "active_listeners": len(self.active_listeners)
        }

# Store discussion managers
discussion_managers: Dict[str, DiscussionManager] = {}

@router.post("/create")
async def create_discussion(
    request: UnifiedDiscussionCreateRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new discussion session with any number of agents.
    """
    try:
        # Extract request parameters
        num_agents = request.num_agents
        title = request.title or "Discussion"
        system_prompt = request.system_prompt or "You are participating in a discussion with AI agents."
        tags = request.tags or []
        agent_names = request.agent_names
        agent_roles = request.agent_roles
        agent_models = request.agent_models
        chair_role = request.chair_role or "Claude"

        # Generate session ID
        session_id = str(uuid4())

        # Create session in database
        session = Session(
            id=session_id,
            system_prompt=system_prompt,
            title=title,
            tags=json.dumps(tags) if tags else None,
            is_multi_agent=(num_agents > 1)
        )
        db.add(session)
        await db.flush()

        # Create agents in database
        for i in range(num_agents):
            agent_name = agent_names[i] if agent_names and i < len(agent_names) else f"Agent {i+1}"
            agent_role = agent_roles[i] if agent_roles and i < len(agent_roles) else f"Assistant {i+1}"
            agent_model = agent_models[i] if agent_models and i < len(agent_models) else None

            agent = Agent(
                session_id=session_id,
                agent_index=i,
                name=agent_name,
                role=agent_role,
                model=agent_model
            )
            db.add(agent)

        await db.commit()

        # Create discussion manager
        manager = DiscussionManager(session_id, system_prompt, chair_role)

        # Add agents to discussion
        for i in range(num_agents):
            agent_name = agent_names[i] if agent_names and i < len(agent_names) else f"Agent {i+1}"
            agent_role = agent_roles[i] if agent_roles and i < len(agent_roles) else f"Assistant {i+1}"
            agent_model = agent_models[i] if agent_models and i < len(agent_models) else None

            agent_id = f"{session_id}_{i}"
            manager.add_participant(agent_id, agent_name, agent_role, agent_model)

        # Store manager
        discussion_managers[session_id] = manager

        logger.info(f"Created discussion {session_id} with {num_agents} agents")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating discussion: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating discussion: {str(e)}")

@router.post("/message")
async def send_message(
    request: UnifiedDiscussionMessageRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message to a discussion.
    """
    try:
        # Extract request parameters
        session_id = request.session_id
        message = request.message
        context = request.context
        question = request.question
        sender = request.initiator
        target_agents = request.target_agents

        # Validate parameters
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        if not message:
            raise HTTPException(status_code=400, detail="message is required")

        # Get discussion manager
        manager = discussion_managers.get(session_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Discussion not found")

        # Add message to discussion
        user_message = manager.add_message(sender, message, "user_message")

        # Determine target agents
        if target_agents:
            participants = [manager.get_participant(f"{session_id}_{i}") for i in target_agents]
            participants = [p for p in participants if p]
        else:
            participants = manager.get_all_participants()

        # Create tasks for agent responses
        for participant in participants:
            # Create task for agent response
            asyncio.create_task(
                manager.get_agent_response(participant.agent_id, message, context, question)
            )

        # Return immediately, responses will be streamed
        return {
            "session_id": session_id,
            "message_id": user_message["id"],
            "target_agents": [p.agent_id for p in participants]
        }
    except Exception as e:
        logger.error(f"Error sending message to discussion: {e}")
        raise HTTPException(status_code=500, detail=f"Error sending message: {str(e)}")

@router.get("/stream/{session_id}")
async def stream_discussion(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Stream messages from a discussion.
    """
    try:
        # Get discussion manager
        manager = discussion_managers.get(session_id)
        if not manager:
            raise HTTPException(status_code=404, detail="Discussion not found")

        # Create streaming response
        async def discussion_stream():
            # Add listener
            queue = manager.add_listener()

            try:
                # Send initial event with discussion state
                initial_state = {
                    "type": "initial_state",
                    "session_id": session_id,
                    "participants": [p.to_dict() for p in manager.get_all_participants()],
                    "history": manager.message_history
                }
                yield f"data: {json.dumps(initial_state)}\n\n"

                # Stream messages
                while True:
                    try:
                        # Wait for new messages
                        message = await queue.get()

                        # Send message event
                        yield f"data: {json.dumps({'type': 'message', 'content': message})}\n\n"
                    except asyncio.CancelledError:
                        break
            finally:
                # Remove listener
                manager.remove_listener(queue)

        return StreamingResponse(
            discussion_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in Nginx
            }
        )
    except Exception as e:
        logger.error(f"Error streaming discussion: {e}")
        raise HTTPException(status_code=500, detail=f"Error streaming discussion: {str(e)}")
