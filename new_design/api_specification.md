# API Specification

This document outlines the API endpoints for the Autonomous Agent System.

## Base URL

All API endpoints are relative to the base URL: `/api/v1`

## Authentication

All API requests require authentication using an API key provided in the `Authorization` header:

```
Authorization: Bearer YOUR_API_KEY
```

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Authentication failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include a JSON body with error details:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}  // Optional additional details
  }
}
```

## Task Management

### Create a Task

**POST** `/tasks`

Create a new task for agents to work on.

**Request Body:**

```json
{
  "title": "Task title",
  "description": "Detailed task description",
  "complexity": 5,  // 1-10 scale
  "priority": 3     // 1-10 scale, optional (default: 5)
}
```

**Response:**

```json
{
  "id": "task-uuid",
  "title": "Task title",
  "description": "Detailed task description",
  "complexity": 5,
  "status": "not_started",
  "stage_progress": 0,
  "created_at": "2023-05-12T10:30:00Z",
  "updated_at": "2023-05-12T10:30:00Z",
  "completed_at": null,
  "assigned_agent_id": null,
  "result_path": null,
  "priority": 3
}
```

### List Tasks

**GET** `/tasks`

Retrieve a list of tasks with optional filtering.

**Query Parameters:**

- `status` - Filter by status (e.g., `not_started`, `design`, `build`, etc.)
- `agent_id` - Filter by assigned agent
- `limit` - Maximum number of tasks to return (default: 20)
- `offset` - Pagination offset (default: 0)

**Response:**

```json
{
  "total": 42,
  "limit": 20,
  "offset": 0,
  "tasks": [
    {
      "id": "task-uuid-1",
      "title": "Task 1",
      "description": "Task 1 description",
      "complexity": 5,
      "status": "design",
      "stage_progress": 60,
      "created_at": "2023-05-12T10:30:00Z",
      "updated_at": "2023-05-12T11:15:00Z",
      "completed_at": null,
      "assigned_agent_id": "agent-uuid-1",
      "result_path": null,
      "priority": 3
    },
    // More tasks...
  ]
}
```

### Get Task Details

**GET** `/tasks/{task_id}`

Retrieve detailed information about a specific task.

**Response:**

```json
{
  "id": "task-uuid",
  "title": "Task title",
  "description": "Detailed task description",
  "complexity": 5,
  "status": "design",
  "stage_progress": 60,
  "created_at": "2023-05-12T10:30:00Z",
  "updated_at": "2023-05-12T11:15:00Z",
  "completed_at": null,
  "assigned_agent_id": "agent-uuid",
  "result_path": null,
  "priority": 3,
  "updates": [
    {
      "id": "update-uuid",
      "agent_id": "agent-uuid",
      "update_type": "status_change",
      "content": "Task moved to design stage",
      "timestamp": "2023-05-12T10:35:00Z"
    }
    // More updates...
  ]
}
```

### Update Task Status

**PUT** `/tasks/{task_id}/status`

Update the status of a task.

**Request Body:**

```json
{
  "status": "build",
  "stage_progress": 25,
  "update_message": "Moving to build phase after completing design"
}
```

**Response:**

```json
{
  "id": "task-uuid",
  "status": "build",
  "stage_progress": 25,
  "updated_at": "2023-05-12T14:20:00Z"
}
```

### Get Task Updates

**GET** `/tasks/{task_id}/updates`

Retrieve the history of updates for a specific task.

**Query Parameters:**

- `limit` - Maximum number of updates to return (default: 20)
- `offset` - Pagination offset (default: 0)

**Response:**

```json
{
  "total": 5,
  "limit": 20,
  "offset": 0,
  "updates": [
    {
      "id": "update-uuid-1",
      "agent_id": "agent-uuid",
      "update_type": "status_change",
      "content": "Task moved to build stage",
      "timestamp": "2023-05-12T14:20:00Z"
    },
    // More updates...
  ]
}
```

## Agent Management

### List Agents

**GET** `/agents`

Retrieve a list of all agents.

**Query Parameters:**

- `status` - Filter by status (e.g., `available`, `busy`, `offline`)
- `model` - Filter by model type
- `limit` - Maximum number of agents to return (default: 20)
- `offset` - Pagination offset (default: 0)

**Response:**

```json
{
  "total": 10,
  "limit": 20,
  "offset": 0,
  "agents": [
    {
      "id": "agent-uuid-1",
      "name": "Agent 1",
      "model": "gemma3-4b",
      "endpoint": "localhost:11434",
      "status": "available",
      "min_complexity": 1,
      "max_complexity": 5,
      "created_at": "2023-05-01T00:00:00Z",
      "last_active": "2023-05-12T15:30:00Z"
    },
    // More agents...
  ]
}
```

### Get Agent Details

**GET** `/agents/{agent_id}`

Retrieve detailed information about a specific agent.

**Response:**

```json
{
  "id": "agent-uuid",
  "name": "Agent 1",
  "model": "gemma3-4b",
  "endpoint": "localhost:11434",
  "status": "busy",
  "min_complexity": 1,
  "max_complexity": 5,
  "workspace_path": "/agent_workspaces/agent-uuid",
  "created_at": "2023-05-01T00:00:00Z",
  "last_active": "2023-05-12T15:30:00Z",
  "current_tasks": [
    {
      "id": "task-uuid",
      "title": "Task title",
      "status": "build",
      "stage_progress": 25
    }
  ],
  "tools": [
    {
      "id": "tool-uuid",
      "name": "Terminal",
      "type": "terminal",
      "permissions": "read-write"
    }
    // More tools...
  ]
}
```

### Update Agent Status

**PUT** `/agents/{agent_id}/status`

Update the status of an agent.

**Request Body:**

```json
{
  "status": "available"
}
```

**Response:**

```json
{
  "id": "agent-uuid",
  "status": "available",
  "last_active": "2023-05-12T16:45:00Z"
}
```

### Get Agent Tasks

**GET** `/agents/{agent_id}/tasks`

Retrieve tasks assigned to a specific agent.

**Query Parameters:**

- `status` - Filter by task status
- `limit` - Maximum number of tasks to return (default: 20)
- `offset` - Pagination offset (default: 0)

**Response:**

```json
{
  "total": 3,
  "limit": 20,
  "offset": 0,
  "tasks": [
    {
      "id": "task-uuid-1",
      "title": "Task 1",
      "status": "build",
      "stage_progress": 25,
      "created_at": "2023-05-12T10:30:00Z",
      "updated_at": "2023-05-12T14:20:00Z"
    },
    // More tasks...
  ]
}
```

## Workspace Management

### List Workspace Files

**GET** `/workspaces/{workspace_id}/files`

List files in an agent's workspace.

**Query Parameters:**

- `path` - Subdirectory path (optional)

**Response:**

```json
{
  "workspace_id": "workspace-uuid",
  "path": "/tasks/task-uuid/src",
  "files": [
    {
      "name": "main.py",
      "type": "file",
      "size": 1024,
      "last_modified": "2023-05-12T15:00:00Z"
    },
    {
      "name": "data",
      "type": "directory",
      "last_modified": "2023-05-12T14:30:00Z"
    }
    // More files...
  ]
}
```

### Get File Content

**GET** `/workspaces/{workspace_id}/files/{file_path}`

Retrieve the content of a file in the workspace.

**Response:**

The file content with appropriate Content-Type header.

### Upload File

**POST** `/workspaces/{workspace_id}/files`

Upload a file to the workspace.

**Request:**

Multipart form data with:
- `file` - The file to upload
- `path` - Destination path within the workspace (optional)

**Response:**

```json
{
  "name": "uploaded_file.txt",
  "path": "/tasks/task-uuid/src/uploaded_file.txt",
  "size": 1024,
  "last_modified": "2023-05-12T17:00:00Z"
}
```

## Human-AI Discussion API

### Create Discussion Session

**POST** `/discussions`

Create a new discussion session.

**Request Body:**

```json
{
  "title": "Discussion title",
  "system_prompt": "Optional system prompt",
  "tags": ["tag1", "tag2"]
}
```

**Response:**

```json
{
  "id": "session-uuid",
  "title": "Discussion title",
  "system_prompt": "Optional system prompt",
  "created_at": "2023-05-12T17:30:00Z",
  "updated_at": "2023-05-12T17:30:00Z",
  "status": "active",
  "tags": ["tag1", "tag2"]
}
```

### Send Message

**POST** `/discussions/{session_id}/messages`

Send a message in a discussion.

**Request Body:**

```json
{
  "role": "user",
  "content": "Message content",
  "metadata": {}  // Optional
}
```

**Response:**

```json
{
  "id": "message-uuid",
  "role": "user",
  "content": "Message content",
  "timestamp": "2023-05-12T17:35:00Z",
  "metadata": {}
}
```

### Get Messages

**GET** `/discussions/{session_id}/messages`

Retrieve messages from a discussion.

**Query Parameters:**

- `limit` - Maximum number of messages to return (default: 50)
- `before` - Retrieve messages before this timestamp
- `after` - Retrieve messages after this timestamp

**Response:**

```json
{
  "session_id": "session-uuid",
  "messages": [
    {
      "id": "message-uuid-1",
      "role": "user",
      "content": "User message",
      "timestamp": "2023-05-12T17:35:00Z"
    },
    {
      "id": "message-uuid-2",
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": "2023-05-12T17:35:10Z"
    }
    // More messages...
  ]
}
```

### Stream Messages

**GET** `/discussions/{session_id}/stream`

Stream messages from a discussion in real-time using Server-Sent Events.

**Response:**

Server-Sent Events stream with message events.
