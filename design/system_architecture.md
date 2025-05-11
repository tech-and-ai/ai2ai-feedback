# AI-to-AI Feedback System Architecture

## Overview

The AI-to-AI Feedback System is designed to enable multiple AI agents to collaborate, delegate tasks, and provide feedback to each other. The system is built on a FastAPI backend with SQLite database storage, supporting asynchronous processing and real-time communication between agents.

## Core Components

### 1. Multi-Agent System

The multi-agent system allows creating sessions with any number of AI agents, each with its own role, name, and potentially different underlying model. Agents can:

- Process messages and tasks
- Delegate subtasks to other agents
- Provide feedback on each other's work
- Store and retrieve context information
- Complete tasks with detailed results

### 2. Task Management

Tasks are the primary unit of work in the system. Each task has:

- A title and description
- Status tracking (pending, in-progress, completed, failed)
- Assignment to specific agents
- Parent-child relationships for subtasks
- Context entries for storing information
- Updates for tracking progress

### 3. Agent Loops

Each agent runs in its own asynchronous loop, which:

- Regularly checks for assigned tasks
- Processes new tasks or continues existing ones
- Interacts with AI models to generate responses
- Updates task status and context
- Delegates subtasks when appropriate

### 4. Model Providers

The system supports multiple AI model providers:

- OpenRouter (default)
- Anthropic
- OpenAI
- Ollama (local models)

Each provider implements a common interface for generating completions and streaming responses.

## Data Flow

1. **Session Creation**: A user creates a multi-agent session with a specified number of agents
2. **Agent Initialization**: Agent loops are started for each agent in the session
3. **Message Sending**: A user sends a message to the session, creating tasks for agents
4. **Task Processing**: Agents process their tasks, potentially delegating subtasks
5. **Response Collection**: Completed task results are collected and can be retrieved via API

## API Endpoints

### Multi-Agent Endpoints

- `POST /multi-agent/create`: Create a new multi-agent session
- `POST /multi-agent/message`: Send a message to a multi-agent session
- `GET /multi-agent/tasks/{session_id}`: Get all tasks for a session
- `GET /multi-agent/agents/{session_id}`: Get all agents for a session
- `POST /multi-agent/agents/{session_id}/restart/{agent_index}`: Restart an agent's task loop
- `POST /multi-agent/agents/{session_id}/start_all`: Start all agent loops for a session
- `GET /multi-agent/responses/{session_id}`: Get all completed task responses for a session

### Feedback Endpoints

- `POST /feedback`: Get direct feedback from a larger model
- `POST /feedback/stream`: Get streaming direct feedback
- `POST /session/feedback`: Get feedback with session context
- `POST /session/feedback/stream`: Get streaming feedback with session context

## Database Schema

### Sessions

- `id`: Unique session identifier
- `system_prompt`: Optional system prompt for the session
- `title`: Optional title for the session
- `tags`: Optional tags for categorization
- `is_multi_agent`: Whether this is a multi-agent session
- `created_at`: Timestamp of creation

### Agents

- `id`: Unique agent identifier
- `session_id`: Session this agent belongs to
- `agent_index`: Index of the agent in the session
- `name`: Name of the agent
- `role`: Role of the agent
- `model`: Model used by the agent

### Tasks

- `id`: Unique task identifier
- `title`: Task title
- `description`: Task description
- `status`: Task status (pending, in_progress, completed, failed)
- `created_by`: Who created the task
- `assigned_to`: Agent assigned to the task
- `created_at`: Timestamp of creation
- `updated_at`: Timestamp of last update
- `completed_at`: Timestamp of completion
- `result`: Task result
- `parent_task_id`: Parent task ID for subtasks
- `session_id`: Session this task belongs to

### Task Context

- `id`: Unique context entry identifier
- `task_id`: Task this context belongs to
- `key`: Context key
- `value`: Context value

### Task Updates

- `id`: Unique update identifier
- `task_id`: Task this update belongs to
- `agent_id`: Agent who made the update
- `content`: Update content
- `timestamp`: Timestamp of the update

## Technical Implementation

### Asynchronous Processing

The system uses Python's asyncio for asynchronous processing, allowing:

- Multiple agent loops to run concurrently
- Non-blocking API endpoints
- Efficient database access with SQLAlchemy's async support

### Background Tasks

FastAPI's BackgroundTasks are used to start agent loops without blocking the API response. Each agent loop is managed as an asyncio task with proper error handling and cleanup.

### Task Delegation

Agents can delegate tasks to other agents by:
1. Creating a new task with a parent-child relationship
2. Assigning it to another agent by name, role, or ID
3. Adding context entries to track delegation

### Context Management

The system maintains context through:
- Task context entries (key-value pairs)
- Task updates (timestamped progress reports)
- Parent-child relationships between tasks
