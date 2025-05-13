"""
Main module for AI-to-AI Feedback API

A lightweight FastAPI server that provides AI-to-AI feedback functionality.
This API allows one AI model to request feedback from a more powerful model
to improve its reasoning and problem-solving capabilities.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession

from . import __version__
from .database import init_db, get_db, create_session, get_session, add_message, add_feedback
from .multi_agent import router as multi_agent_router
from .realtime_discussion import router as realtime_discussion_router
from .unified_discussion import router as unified_discussion_router
from .autonomous_api import router as autonomous_router
from .project_api import router as project_router
from .job_manager_api import router as job_manager_router
from .models import (
    FeedbackRequest, FeedbackResponse,
    SessionCreateRequest, SessionCreateResponse,
    SessionFeedbackRequest, SessionProcessRequest, ProcessResponse,
    SessionEndRequest, SessionEndResponse,
    UnifiedDiscussionCreateRequest, UnifiedDiscussionMessageRequest
)
from .providers.factory import get_model_provider
from .utils.feedback_parser import extract_structured_feedback, StreamingFeedbackParser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai2ai-feedback")

# Create FastAPI app
app = FastAPI(
    title="AI-to-AI Feedback API",
    description="API for AI-to-AI feedback to improve reasoning and problem-solving",
    version=__version__,
)

# Add CORS middleware
# Configure CORS with more specific settings
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8001",
    "*"  # Allow all origins for development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Requested-With", "Authorization"],
)

# Include routers
app.include_router(multi_agent_router)
app.include_router(realtime_discussion_router)
app.include_router(unified_discussion_router)
app.include_router(autonomous_router)
app.include_router(project_router, prefix="/projects", tags=["projects"])
app.include_router(job_manager_router, tags=["job-manager"])

# Mount static files directory
static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Mount app static files directory
app_static_dir = Path(__file__).parent / "static"
app_static_dir.mkdir(exist_ok=True)
app.mount("/app/static", StaticFiles(directory=str(app_static_dir)), name="app_static")

# Import controller and worker initialization
from .controller_init import start_controller_agent, stop_controller_agent
from .worker_init import start_worker_agents, stop_worker_agents

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the database and controller agent on startup"""
    logger.info("Initializing database...")
    await init_db()
    logger.info("Database initialized")

    # Start controller agent
    logger.info("Starting controller agent...")
    success = await start_controller_agent()
    if success:
        logger.info("Controller agent started successfully")
    else:
        logger.warning("Failed to start controller agent")

    # Start worker agents
    logger.info("Starting worker agents...")
    success = await start_worker_agents()
    if success:
        logger.info("Worker agents started successfully")
    else:
        logger.warning("Failed to start worker agents")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Stop the agents on shutdown"""
    # Stop controller agent
    logger.info("Stopping controller agent...")
    success = await stop_controller_agent()
    if success:
        logger.info("Controller agent stopped successfully")
    else:
        logger.warning("Failed to stop controller agent")

    # Stop worker agents
    logger.info("Stopping worker agents...")
    success = await stop_worker_agents()
    if success:
        logger.info("Worker agents stopped successfully")
    else:
        logger.warning("Failed to stop worker agents")

# Root endpoint - API information
@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Get basic API information or serve the streaming client.
    """
    # Check if the request accepts HTML
    client_path = static_dir / "streaming_client.html"
    if client_path.exists():
        return client_path.read_text()

    # Fallback to JSON response
    return {
        "name": "AI-to-AI Feedback API",
        "version": __version__,
        "description": "API for AI-to-AI feedback to improve reasoning and problem-solving",
        "endpoints": [
            {"path": "/", "method": "GET", "description": "Get API information"},
            {"path": "/models", "method": "GET", "description": "Get available models"},
            {"path": "/feedback", "method": "POST", "description": "Get direct feedback"},
            {"path": "/feedback/stream", "method": "POST", "description": "Get streaming direct feedback"},
            {"path": "/session/create", "method": "POST", "description": "Create a new session"},
            {"path": "/session/feedback", "method": "POST", "description": "Get feedback with session context"},
            {"path": "/session/feedback/stream", "method": "POST", "description": "Get streaming feedback with session context"},
            {"path": "/session/process", "method": "POST", "description": "Process text with potential feedback"},
            {"path": "/session/end", "method": "POST", "description": "End a session"},
            {"path": "/multi-agent", "method": "GET", "description": "Multi-agent conversation interface"},
            {"path": "/discussion/create", "method": "POST", "description": "Create a unified discussion with any number of agents"},
            {"path": "/discussion/message", "method": "POST", "description": "Send a message to a unified discussion"},
            {"path": "/discussion/stream/{session_id}", "method": "GET", "description": "Stream messages from a unified discussion"},
            {"path": "/realtime-discussion/create", "method": "POST", "description": "Create a real-time discussion with multiple agents"},
            {"path": "/realtime-discussion/message", "method": "POST", "description": "Send a message to a real-time discussion"},
            {"path": "/realtime-discussion/stream/{session_id}", "method": "GET", "description": "Stream messages from a real-time discussion"}
        ]
    }

@app.get("/multi-agent-client", response_class=HTMLResponse)
async def get_multi_agent_client():
    """Serve the multi-agent client HTML page"""
    client_path = static_dir / "multi_agent_client.html"
    if client_path.exists():
        return client_path.read_text()

    raise HTTPException(status_code=404, detail="Multi-agent client not found")

@app.get("/discussion-client", response_class=HTMLResponse)
async def get_discussion_client():
    """Serve the discussion client HTML page"""
    client_path = static_dir / "discussion_client.html"
    if client_path.exists():
        return client_path.read_text()

    raise HTTPException(status_code=404, detail="Discussion client not found")

@app.get("/autonomous-client", response_class=HTMLResponse)
async def get_autonomous_client():
    """Serve the autonomous agent client HTML page"""
    client_path = static_dir / "autonomous_client.html"
    if client_path.exists():
        return client_path.read_text()

    raise HTTPException(status_code=404, detail="Autonomous agent client not found")

@app.get("/job-manager", response_class=HTMLResponse)
async def get_job_manager():
    """Serve the job manager UI page"""
    client_path = Path(__file__).parent / "static" / "job_manager.html"
    if client_path.exists():
        return client_path.read_text()

    raise HTTPException(status_code=404, detail="Job manager UI not found")

# Get available models
@app.get("/models")
async def get_models():
    """
    Get available models.
    """
    try:
        provider = get_model_provider()
        return {
            "provider": provider.get_provider_name(),
            "model": provider.get_model_name()
        }
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting models: {str(e)}")

# Get direct feedback
@app.post("/feedback", response_model=FeedbackResponse)
async def get_feedback(request: FeedbackRequest, background_tasks: BackgroundTasks = None):
    """
    Get feedback from a larger model on your current reasoning.
    """
    try:
        logger.info(f"Requesting feedback: {request.question[:50]}...")

        # Get the model provider
        provider = get_model_provider()

        # Create system prompt for the consultation model
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
        user_prompt = f"""
The assistant is working on a problem and has requested feedback. Here is their current reasoning:

{request.context}

Specific feedback request: {request.question}
"""

        # Get feedback from the consultation model
        feedback_text = await provider.generate_completion(system_prompt, user_prompt)

        # Extract structured feedback
        structured = extract_structured_feedback(feedback_text)

        # Create response
        result = {
            "feedback": feedback_text,
            "structured": structured,
            "metadata": {
                "source_model": provider.get_model_name(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        logger.info(f"Feedback received: {structured.get('FEEDBACK_SUMMARY', '')[:50]}...")
        return result
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting feedback: {str(e)}")

# Get streaming direct feedback
@app.post("/feedback/stream")
async def get_feedback_stream(request: FeedbackRequest):
    """
    Get streaming feedback from a larger model on your current reasoning.
    """
    try:
        logger.info(f"Requesting streaming feedback: {request.question[:50]}...")

        # Get the model provider
        provider = get_model_provider()

        # Create system prompt for the consultation model
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
        user_prompt = f"""
The assistant is working on a problem and has requested feedback. Here is their current reasoning:

{request.context}

Specific feedback request: {request.question}
"""

        # Create streaming response
        async def feedback_generator():
            parser = StreamingFeedbackParser()
            metadata = {
                "source_model": provider.get_model_name(),
                "timestamp": datetime.utcnow().isoformat()
            }

            # Send initial event with metadata
            yield f"data: {json.dumps({'type': 'metadata', 'content': metadata})}\n\n"

            try:
                # Stream feedback from the consultation model
                async for chunk in provider.generate_completion_stream(system_prompt, user_prompt):
                    # Process the chunk
                    sections, updated_section, added_content = parser.process_chunk(chunk)

                    # Send the chunk event
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                    # If a section was updated, send a section update event
                    if updated_section and added_content:
                        yield f"data: {json.dumps({'type': 'section_update', 'section': updated_section, 'content': added_content, 'sections': sections})}\n\n"

                # Send the complete structured feedback
                structured = parser.get_result()
                yield f"data: {json.dumps({'type': 'structured', 'content': structured})}\n\n"

                # Send completion event
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                logger.info(f"Streaming feedback completed: {structured.get('FEEDBACK_SUMMARY', '')[:50]}...")
            except Exception as e:
                # Send error event
                error_msg = str(e)
                logger.error(f"Error streaming feedback: {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

        return StreamingResponse(
            feedback_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in Nginx
            }
        )
    except Exception as e:
        logger.error(f"Error setting up streaming feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting up streaming feedback: {str(e)}")

# Create a new session
@app.post("/session/create", response_model=SessionCreateResponse)
async def create_session_endpoint(request: SessionCreateRequest, db: AsyncSession = Depends(get_db)):
    """
    Create a new session for ongoing interactions.
    """
    try:
        session_id = str(uuid4())

        # Create session in database
        success = await create_session(
            db,
            session_id,
            request.system_prompt,
            request.title,
            request.tags
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create session")

        logger.info(f"Created session {session_id}")
        return {"session_id": session_id}
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")

# Get feedback with session context
@app.post("/session/feedback", response_model=FeedbackResponse)
async def session_feedback(request: SessionFeedbackRequest, db: AsyncSession = Depends(get_db)):
    """
    Request feedback from a larger model with context from previous interactions.
    """
    try:
        # Get session from database
        session = await get_session(db, request.session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        logger.info(f"Requesting feedback for session {request.session_id}: {request.question[:50]}...")

        # Add the current interaction to the session history
        message_id = await add_message(
            db,
            request.session_id,
            "user",
            f"Context: {request.context}\nQuestion: {request.question}"
        )

        if not message_id:
            raise HTTPException(status_code=500, detail="Failed to add message to session")

        # Get the model provider
        provider = get_model_provider()

        # Create system prompt for the consultation model
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

The conversation history is provided for context. Focus on the most recent question.
"""

        # Format the history as a conversation
        formatted_history = ""
        if session.get("history"):
            formatted_history = "\n\n".join([
                f"{entry['role'].capitalize()}: {entry['content']}"
                for entry in session["history"]
                if entry["role"] != "system"
            ])

        # Create user prompt with history
        user_prompt = f"""
Conversation history:
{formatted_history}

The assistant is working on a problem and has requested feedback. Here is their current reasoning:

{request.context}

Specific feedback request: {request.question}
"""

        # Get feedback from the consultation model
        feedback_text = await provider.generate_completion(system_prompt, user_prompt)

        # Extract structured feedback
        structured = extract_structured_feedback(feedback_text)

        # Add the response to the session history
        assistant_message_id = await add_message(db, request.session_id, "assistant", feedback_text)

        if not assistant_message_id:
            logger.warning(f"Failed to add assistant message to session {request.session_id}")

        # Add feedback to database
        feedback_id = await add_feedback(db, message_id, feedback_text, structured, provider.get_model_name())

        if not feedback_id:
            logger.warning(f"Failed to add feedback to database for message {message_id}")

        # Create response
        result = {
            "feedback": feedback_text,
            "structured": structured,
            "metadata": {
                "source_model": provider.get_model_name(),
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        logger.info(f"Feedback received for session {request.session_id}: {structured.get('FEEDBACK_SUMMARY', '')[:50]}...")
        return result
    except Exception as e:
        logger.error(f"Error getting session feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting session feedback: {str(e)}")

# Get streaming feedback with session context
@app.post("/session/feedback/stream")
async def session_feedback_stream(request: SessionFeedbackRequest, db: AsyncSession = Depends(get_db)):
    """
    Request streaming feedback from a larger model with context from previous interactions.
    """
    try:
        # Get session from database
        session = await get_session(db, request.session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        logger.info(f"Requesting streaming feedback for session {request.session_id}: {request.question[:50]}...")

        # Add the current interaction to the session history
        message_id = await add_message(
            db,
            request.session_id,
            "user",
            f"Context: {request.context}\nQuestion: {request.question}"
        )

        if not message_id:
            raise HTTPException(status_code=500, detail="Failed to add message to session")

        # Get the model provider
        provider = get_model_provider()

        # Create system prompt for the consultation model
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

The conversation history is provided for context. Focus on the most recent question.
"""

        # Format the history as a conversation
        formatted_history = ""
        if session.get("history"):
            formatted_history = "\n\n".join([
                f"{entry['role'].capitalize()}: {entry['content']}"
                for entry in session["history"]
                if entry["role"] != "system"
            ])

        # Create user prompt with history
        user_prompt = f"""
Conversation history:
{formatted_history}

The assistant is working on a problem and has requested feedback. Here is their current reasoning:

{request.context}

Specific feedback request: {request.question}
"""

        # Create streaming response
        async def feedback_generator():
            parser = StreamingFeedbackParser()
            complete_feedback = ""
            metadata = {
                "source_model": provider.get_model_name(),
                "timestamp": datetime.utcnow().isoformat(),
                "session_id": request.session_id
            }

            # Send initial event with metadata
            yield f"data: {json.dumps({'type': 'metadata', 'content': metadata})}\n\n"

            try:
                # Stream feedback from the consultation model
                async for chunk in provider.generate_completion_stream(system_prompt, user_prompt):
                    # Process the chunk
                    sections, updated_section, added_content = parser.process_chunk(chunk)
                    complete_feedback += chunk

                    # Send the chunk event
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                    # If a section was updated, send a section update event
                    if updated_section and added_content:
                        yield f"data: {json.dumps({'type': 'section_update', 'section': updated_section, 'content': added_content, 'sections': sections})}\n\n"

                # Get the final structured feedback
                structured = parser.get_result()

                # Send the complete structured feedback
                yield f"data: {json.dumps({'type': 'structured', 'content': structured})}\n\n"

                # Add the complete response to the session history
                assistant_message_id = await add_message(db, request.session_id, "assistant", complete_feedback)

                if not assistant_message_id:
                    logger.warning(f"Failed to add assistant message to session {request.session_id}")

                # Add feedback to database
                feedback_id = await add_feedback(db, message_id, complete_feedback, structured, provider.get_model_name())

                if not feedback_id:
                    logger.warning(f"Failed to add feedback to database for message {message_id}")

                # Send completion event
                yield f"data: {json.dumps({'type': 'done'})}\n\n"

                logger.info(f"Streaming feedback completed for session {request.session_id}: {structured.get('FEEDBACK_SUMMARY', '')[:50]}...")
            except Exception as e:
                # Send error event
                error_msg = str(e)
                logger.error(f"Error streaming feedback for session {request.session_id}: {error_msg}")
                yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"

        return StreamingResponse(
            feedback_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable buffering in Nginx
            }
        )
    except Exception as e:
        logger.error(f"Error setting up streaming feedback for session {request.session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error setting up streaming feedback: {str(e)}")

# Process text with potential feedback
@app.post("/session/process", response_model=ProcessResponse)
async def process_text(request: SessionProcessRequest, db: AsyncSession = Depends(get_db)):
    """
    Process text through a smaller model with feedback from a larger model when needed.
    """
    try:
        # Get session from database
        session = await get_session(db, request.session_id)

        if not session:
            raise HTTPException(status_code=404, detail="Session not found or expired")

        logger.info(f"Processing text for session {request.session_id}")

        # Add the user input to the session history
        message_id = await add_message(db, request.session_id, "user", request.text)

        if not message_id:
            raise HTTPException(status_code=500, detail="Failed to add message to session")

        # Create response (simplified for now)
        result = {
            "response": "This endpoint is not fully implemented yet. It will process text and automatically request feedback when needed.",
            "metadata": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }

        logger.info(f"Processed text for session {request.session_id}")
        return result
    except Exception as e:
        logger.error(f"Error processing text: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing text: {str(e)}")

# End a session
@app.post("/session/end", response_model=SessionEndResponse)
async def end_session(request: SessionEndRequest, db: AsyncSession = Depends(get_db)):
    """
    End a session and release its resources.
    """
    try:
        # Check if session exists
        session = await get_session(db, request.session_id)
        success = bool(session)

        logger.info(f"Ended session {request.session_id}: {success}")
        return {"success": success}
    except Exception as e:
        logger.error(f"Error ending session: {e}")
        raise HTTPException(status_code=500, detail=f"Error ending session: {str(e)}")

# Run the application
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8001"))

    logger.info(f"Starting AI-to-AI Feedback API on {host}:{port}")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
