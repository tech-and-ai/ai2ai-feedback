#!/usr/bin/env python3
"""
AI2AI Discussion API

This module provides a simple API for AI2AI discussions.
"""

import os
import json
import logging
import uuid
import asyncio
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from dataclasses import dataclass, field, asdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration
OLLAMA_BASE_URL = "http://192.168.0.77:11434"  # Ollama server URL

# Models
@dataclass
class Agent:
    """Agent model."""
    name: str
    role: str
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Message:
    """Message model."""
    content: str
    sender: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Discussion:
    """Discussion model."""
    title: str
    agents: List[Agent]
    system_prompt: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

# In-memory storage
discussions: Dict[str, Discussion] = {}

# Create Flask app
app = Flask(__name__)
CORS(app)

# API routes
@app.route('/discussion/create', methods=['POST'])
def create_discussion():
    """
    Create a new discussion.

    Returns:
        Discussion ID
    """
    data = request.json

    agents = [Agent(**agent) for agent in data.get('agents', [])]

    discussion = Discussion(
        title=data.get('title', 'Discussion'),
        agents=agents,
        system_prompt=data.get('system_prompt', ''),
        metadata=data.get('metadata', {})
    )

    discussions[discussion.id] = discussion

    logger.info(f"Created discussion: {discussion.id}")
    return jsonify({"session_id": discussion.id})

@app.route('/discussion/message', methods=['POST'])
def send_message():
    """
    Send a message to a discussion.

    Returns:
        Success status
    """
    data = request.json
    session_id = data.get('session_id')

    if session_id not in discussions:
        return jsonify({"error": "Discussion not found"}), 404

    discussion = discussions[session_id]

    # Create message
    message = Message(
        content=data.get('content', ''),
        sender=data.get('sender', 'unknown'),
        metadata=data.get('metadata', {})
    )

    # Add message to discussion
    discussion.messages.append(message)

    # If the sender is not an AI agent, generate responses from all AI agents
    if data.get('sender') == "chair" or data.get('sender') == "human":
        for agent in discussion.agents:
            generate_agent_response(session_id, agent, discussion.messages, discussion.system_prompt)

    logger.info(f"Sent message to discussion {session_id}")
    return jsonify({"status": "success"})

@app.route('/discussion/<session_id>', methods=['GET'])
def get_discussion(session_id):
    """
    Get a discussion by ID.

    Args:
        session_id: Discussion ID

    Returns:
        Discussion
    """
    if session_id not in discussions:
        return jsonify({"error": "Discussion not found"}), 404

    return jsonify(asdict(discussions[session_id]))

@app.route('/discussion/<session_id>/messages', methods=['GET'])
def get_messages(session_id):
    """
    Get messages in a discussion.

    Args:
        session_id: Discussion ID

    Returns:
        List of messages
    """
    if session_id not in discussions:
        return jsonify({"error": "Discussion not found"}), 404

    return jsonify([asdict(message) for message in discussions[session_id].messages])

def generate_agent_response(session_id: str, agent: Agent, messages: List[Message], system_prompt: str):
    """
    Generate a response from an AI agent.

    Args:
        session_id: Discussion ID
        agent: Agent to generate response
        messages: List of messages in the discussion
        system_prompt: System prompt for the agent
    """
    # Format messages for the agent
    formatted_messages = format_messages_for_agent(messages, agent, system_prompt)

    # Generate response using Ollama
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": agent.model,
                "prompt": formatted_messages,
                "stream": False
            }
        )

        if response.status_code != 200:
            logger.error(f"Error generating response from {agent.name}: {response.text}")
            return

        result = response.json()
        response_text = result.get("response", "")

        # Create message
        message = Message(
            content=response_text,
            sender=agent.name,
            metadata={"role": agent.role, "model": agent.model}
        )

        # Add message to discussion
        discussions[session_id].messages.append(message)

        logger.info(f"Generated response from {agent.name}")
    except Exception as e:
        logger.error(f"Exception generating response from {agent.name}: {e}")

def format_messages_for_agent(messages: List[Message], agent: Agent, system_prompt: str) -> str:
    """
    Format messages for an agent.

    Args:
        messages: List of messages
        agent: Agent
        system_prompt: System prompt

    Returns:
        Formatted messages
    """
    formatted = f"System: {system_prompt}\n\n"
    formatted += f"You are {agent.name}, a {agent.role}.\n\n"
    formatted += "Here is the conversation so far:\n\n"

    for message in messages:
        formatted += f"{message.sender}: {message.content}\n\n"

    formatted += f"{agent.name}:"

    return formatted

# Add a route for serving the HTML file
@app.route('/')
def index():
    """Serve the index page."""
    return app.send_static_file('ai2ai_discussion.html')

if __name__ == "__main__":
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)

    # Copy HTML file to static directory
    html_path = os.path.join(os.path.dirname(__file__), 'ai2ai_discussion.html')
    static_path = os.path.join(os.path.dirname(__file__), 'static', 'ai2ai_discussion.html')

    if os.path.exists(html_path):
        with open(html_path, 'r') as f:
            html_content = f.read()

        with open(static_path, 'w') as f:
            f.write(html_content)

    app.run(host='0.0.0.0', port=8002, debug=True)
