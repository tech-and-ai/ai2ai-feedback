# Autonomous Agent System

A framework for autonomous AI agents to work on various tasks independently, with each agent capable of handling the entire lifecycle of a task from design to completion.

## Overview

The Autonomous Agent System allows AI agents to handle the entire lifecycle of tasks from design to completion. Each agent has its own workspace with access to tools like terminal commands, Python execution, web search, GitHub integration, and more.

## Key Features

- **Universal Workflow**: All tasks follow the same stages (Design → Build → Test → Review → Complete)
- **Complexity-Based Assignment**: Tasks are assigned to agents based on complexity matching
- **Isolated Workspaces**: Each agent has its own workspace with virtual environments
- **Tool Integration**: Agents have access to various tools for task execution
- **Human-AI Discussion**: API for human-AI discussions

## Getting Started

### Prerequisites

- Python 3.8+
- SQLite or PostgreSQL
- FastAPI
- Uvicorn

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements_new.txt
   ```

3. Run the application:
   ```bash
   uvicorn app.new_main:app --reload --port 8001
   ```

4. Access the application:
   - Dashboard UI: http://localhost:8001/api/v1/dashboard
   - API Documentation: http://localhost:8001/docs

## Usage

### Agent Dashboard

The Agent Dashboard provides a user interface for:

1. Creating and managing tasks
2. Monitoring agent status
3. Viewing task progress
4. Managing discussions

### API Endpoints

The system provides the following API endpoints:

#### Task Management

- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks` - List all tasks
- `GET /api/v1/tasks/{task_id}` - Get task details
- `PUT /api/v1/tasks/{task_id}/status` - Update task status
- `GET /api/v1/tasks/{task_id}/updates` - Get task update history

#### Agent Management

- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `PUT /api/v1/agents/{agent_id}/status` - Update agent status
- `GET /api/v1/agents/{agent_id}/tasks` - Get tasks assigned to an agent

#### Workspace Management

- `POST /api/v1/workspaces` - Create a new workspace
- `GET /api/v1/workspaces/{workspace_id}/files` - List files in workspace
- `POST /api/v1/workspaces/{workspace_id}/files` - Upload file to workspace
- `GET /api/v1/workspaces/{workspace_id}/files/{file_path}` - Get file content

#### Human-AI Discussion

- `POST /api/v1/discussions` - Create a new discussion session
- `POST /api/v1/discussions/{session_id}/messages` - Send a message
- `GET /api/v1/discussions/{session_id}/messages` - Get messages
- `GET /api/v1/discussions/{session_id}/stream` - Stream messages in real-time

## Creating a Task

1. Navigate to the Dashboard UI
2. Click "Create Task" button
3. Fill in the task details:
   - Title
   - Description
   - Complexity (1-10)
   - Priority (1-10)
4. Click "Create Task"

The system will automatically assign the task to an available agent with matching complexity capabilities.

## Adding an Agent

1. Navigate to the Dashboard UI
2. Click "Add Agent" button
3. Fill in the agent details:
   - Name
   - Model (e.g., gemma3-4b, deepseek-coder-v2-16b)
   - Endpoint (e.g., localhost:11434)
   - Complexity Range (min and max)
4. Click "Add Agent"

The agent will be initialized with its own workspace and will be available to pick up tasks.

## Task Workflow

Each task goes through the following stages:

1. **Not Started**: Task is created but not yet assigned
2. **Design**: Agent is planning the approach
3. **Build**: Agent is creating the content/solution
4. **Test**: Agent is verifying it meets requirements
5. **Review**: Agent is performing a final quality check
6. **Complete**: Task is finished and delivered

## Agent Capabilities

Agents can:

- Execute terminal commands
- Run Python code in isolated environments
- Search the web via DuckDuckGo
- Use GitHub for code management
- Generate PDFs and other documents
- Send email notifications
- Create and manage files

## Configuration

The system can be configured through environment variables:

- `DATABASE_URL`: Database connection string
- `SECRET_KEY`: Secret key for JWT tokens
- `AGENT_WORKSPACE_ROOT`: Root directory for agent workspaces
- `OLLAMA_API_URL`: URL for Ollama API
- `OPENROUTER_API_KEY`: API key for OpenRouter (optional)

## Project Structure

```
/app
├── api/
│   ├── routes/
│   │   ├── tasks.py
│   │   ├── agents.py
│   │   ├── workspaces.py
│   │   ├── discussions.py
│   │   └── ui.py
│   ├── models/
│   │   ├── task.py
│   │   ├── agent.py
│   │   ├── workspace.py
│   │   └── discussion.py
│   └── dependencies.py
├── core/
│   ├── config.py
│   ├── security.py
│   └── logging.py
├── db/
│   ├── base.py
│   ├── session.py
│   └── models/
│       ├── task.py
│       ├── agent.py
│       └── discussion.py
├── services/
│   ├── task_service.py
│   ├── agent_service.py
│   ├── workspace_service.py
│   └── discussion_service.py
├── static/
│   ├── agent_dashboard.html
│   └── agent_dashboard.js
└── new_main.py
```

## License

This project is licensed under the MIT License.
