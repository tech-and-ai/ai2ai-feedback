# Autonomous Agent System Architecture

## 1. System Overview

The system provides a framework for autonomous AI agents to work on various tasks independently, with each agent capable of handling the entire lifecycle of a task from design to completion. The system initially uses Ollama models but is designed to scale to more powerful models via OpenRouter API.

## 2. Agent Capabilities

### 2.1 Workspace Management
- Each agent has its own dedicated workspace folder
- Ability to create and manage Python virtual environments (venv)
- File system operations (create/modify/delete files and folders)

### 2.2 Tool Access
- Terminal command execution
- Python script execution
- PDF generation capabilities
- Web search via DuckDuckGo
- GitHub integration (clone, commit, push, pull)
- Database access for task status updates
- Email functionality for notifications

### 2.3 Task Processing
- Agents handle all stages: Design, Build, Test, Review, Complete
- Complexity-based task assignment
- Progress tracking and reporting

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Client Interface                        │
└───────────────────────────────┬─────────────────────────────┘
                                │
┌───────────────────────────────▼─────────────────────────────┐
│                        API Gateway                           │
└───────┬───────────────────────┬───────────────────────┬─────┘
        │                       │                       │
┌───────▼───────┐      ┌────────▼────────┐      ┌──────▼──────┐
│  Task Manager  │      │  Agent Manager  │      │ Tool Manager │
└───────┬───────┘      └────────┬────────┘      └──────┬──────┘
        │                       │                       │
┌───────▼───────────────────────▼───────────────────────▼──────┐
│                         Database Layer                        │
└─────────────────────────────────────────────────────────────┘
```

## 4. Database Schema

### 4.1 Agents Table
```
agents
- id (UUID, primary key)
- name (string)
- model (string, e.g., "gemma3-4b")
- endpoint (string, e.g., "localhost:11434" or "api.openrouter.ai")
- status (enum: available, busy, offline)
- min_complexity (integer)
- max_complexity (integer)
- workspace_path (string)
- created_at (timestamp)
- last_active (timestamp)
```

### 4.2 Tasks Table
```
tasks
- id (UUID, primary key)
- title (string)
- description (text)
- complexity (integer, 1-10)
- status (enum: not_started, design, build, test, review, complete)
- stage_progress (integer, percentage within current stage)
- created_at (timestamp)
- updated_at (timestamp)
- completed_at (timestamp, nullable)
- assigned_agent_id (UUID, foreign key to agents.id, nullable)
- result_path (string, nullable)
- priority (integer)
```

### 4.3 Task Updates Table
```
task_updates
- id (UUID, primary key)
- task_id (UUID, foreign key to tasks.id)
- agent_id (UUID, foreign key to agents.id)
- update_type (enum: status_change, progress_update, note)
- content (text)
- timestamp (timestamp)
```

### 4.4 Agent Workspaces Table
```
agent_workspaces
- id (UUID, primary key)
- agent_id (UUID, foreign key to agents.id)
- task_id (UUID, foreign key to tasks.id)
- workspace_path (string)
- venv_path (string, nullable)
- created_at (timestamp)
- last_accessed (timestamp)
```

## 5. Agent Workspace Structure

Each agent will have a base workspace with the following structure:

```
/agent_workspaces/
  /{agent_id}/
    /global/           # Shared resources across tasks
      /tools/          # Utility scripts and tools
      /references/     # Reference materials
    /tasks/
      /{task_id}/      # Isolated workspace for each task
        /venv/         # Python virtual environment
        /src/          # Source code or content
        /output/       # Generated artifacts
        /research/     # Research materials
        README.md      # Task notes and progress
```

## 6. API Endpoints

### 6.1 Task Management
- `POST /api/tasks` - Create a new task
- `GET /api/tasks` - List all tasks
- `GET /api/tasks/{task_id}` - Get task details
- `PUT /api/tasks/{task_id}/status` - Update task status
- `GET /api/tasks/{task_id}/updates` - Get task update history

### 6.2 Agent Management
- `GET /api/agents` - List all agents
- `GET /api/agents/{agent_id}` - Get agent details
- `PUT /api/agents/{agent_id}/status` - Update agent status
- `GET /api/agents/{agent_id}/tasks` - Get tasks assigned to an agent

### 6.3 Workspace Management
- `POST /api/workspaces` - Create a new workspace
- `GET /api/workspaces/{workspace_id}/files` - List files in workspace
- `POST /api/workspaces/{workspace_id}/files` - Upload file to workspace
- `GET /api/workspaces/{workspace_id}/files/{file_path}` - Get file content

## 7. Tool Integration

### 7.1 Terminal Command Execution
- Secure execution of shell commands within agent workspace
- Command output capture and logging
- Resource usage limits and timeouts

### 7.2 Python Environment
- Automatic venv creation and package management
- Script execution with output capture
- PDF generation via libraries like ReportLab or WeasyPrint

### 7.3 Web Search
- DuckDuckGo API integration for web searches
- Result parsing and extraction
- Rate limiting and caching

### 7.4 GitHub Integration
- Authentication via tokens
- Repository operations (clone, commit, push, pull)
- Issue and PR management

### 7.5 Email Notifications
- SMTP integration for sending emails
- Templated notifications for task completion
- Attachment support for task outputs

## 8. Task Assignment Logic

The system will use a complexity-based assignment algorithm to match tasks with appropriate agents:

1. When a new task is created, its complexity is evaluated (1-10 scale)
2. The system finds available agents whose complexity range includes the task's complexity
3. The first available matching agent is assigned the task
4. The agent's workspace is prepared with necessary tools and resources
5. The agent begins the task at the design stage

## 9. Implementation Plan

### Phase 1: Core Infrastructure
- Database setup
- Basic API endpoints
- Agent workspace management
- Task assignment logic

### Phase 2: Tool Integration
- Terminal command execution
- Python environment management
- Web search capabilities
- Basic file operations

### Phase 3: Advanced Features
- GitHub integration
- Email notifications
- PDF generation
- Advanced research capabilities

### Phase 4: Scaling
- OpenRouter API integration
- Support for more powerful models
- Performance optimizations
- Multi-agent collaboration

## 10. Security Considerations

- Workspace isolation to prevent cross-task contamination
- Rate limiting for external API calls
- Resource usage monitoring and limits
- Secure storage of API keys and credentials
- Input validation and sanitization for all commands
- Regular security audits and updates

## 11. Human-AI Discussion API

The system will maintain the existing API for human-AI discussions, allowing:

- Real-time conversations between humans and AI agents
- Context preservation across interactions
- File sharing and visualization
- Task creation directly from conversations
- Progress monitoring and intervention when needed

This architecture provides a flexible, scalable framework for autonomous agents that can handle a wide variety of tasks while maintaining isolation and security. The system can start with Ollama models and scale to more powerful models as needed.
