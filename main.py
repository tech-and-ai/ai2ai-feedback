#!/usr/bin/env python3
"""
AI2AI Feedback System - Main Entry Point

This module serves as the entry point for the AI2AI Feedback System.
It sets up the application, connects to the database, and starts the API server.
"""

import os
import logging
import argparse
from fastapi import FastAPI
from contextlib import asynccontextmanager

# Import core components
from core.task_manager import TaskManager
from core.agent_manager import AgentManager
from core.model_router import ModelRouter
from core.prompt_manager import PromptManager
from core.output_processor import OutputProcessor

# Import database connection
from db.connection import get_db_connection

# Import API routes
from api.routes import tasks, agents, discussions, outputs

# Import utilities
from utils.logging import setup_logging
from utils.config import load_config

# Setup argument parser
parser = argparse.ArgumentParser(description='AI2AI Feedback System')
parser.add_argument('--config', type=str, default='default', help='Configuration to use (default, development, production)')
parser.add_argument('--debug', action='store_true', help='Enable debug mode')
args = parser.parse_args()

# Load configuration
config = load_config(args.config)

# Setup logging
setup_logging(debug=args.debug)
logger = logging.getLogger(__name__)

# Create FastAPI application
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect to database
    logger.info("Connecting to database...")
    db_connection = get_db_connection(config.database_url)
    
    # Initialize core components
    logger.info("Initializing core components...")
    task_manager = TaskManager(db_connection)
    agent_manager = AgentManager(db_connection)
    model_router = ModelRouter(config.model_providers)
    prompt_manager = PromptManager(config.prompt_templates)
    output_processor = OutputProcessor(db_connection)
    
    # Store components in app state
    app.state.db = db_connection
    app.state.task_manager = task_manager
    app.state.agent_manager = agent_manager
    app.state.model_router = model_router
    app.state.prompt_manager = prompt_manager
    app.state.output_processor = output_processor
    
    logger.info("Application startup complete")
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down application...")
    db_connection.close()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="AI2AI Feedback System",
    description="A system for AI agents to collaborate on tasks",
    version="1.0.0",
    lifespan=lifespan
)

# Include API routes
app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(discussions.router, prefix="/api/discussions", tags=["discussions"])
app.include_router(outputs.router, prefix="/api/outputs", tags=["outputs"])

# Add health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting AI2AI Feedback System with {args.config} configuration")
    
    # Start the API server
    uvicorn.run(
        "main:app",
        host=config.host,
        port=config.port,
        reload=args.debug,
        log_level="debug" if args.debug else "info"
    )
