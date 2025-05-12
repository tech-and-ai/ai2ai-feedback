# Session-Based AI2AI Feedback Tool Design

## Overview

The Session-Based AI2AI Feedback Tool is an enhancement to the existing AI2AI Feedback MCP server that adds support for maintaining context across multiple interactions. This allows for more coherent and contextually aware feedback, especially in complex conversations where previous context is important.

## Goals

1. Maintain conversation context across multiple interactions
2. Provide a way to explicitly create and end sessions
3. Ensure session data is properly managed and cleaned up
4. Maintain compatibility with the existing AI2AI Feedback tools

## Architecture

The Session-Based AI2AI Feedback Tool consists of the following components:

1. **Session Manager**: Responsible for creating, retrieving, updating, and deleting sessions
2. **Session Storage**: Stores session data, including conversation history
3. **Session-Based Tools**: New MCP tools that use sessions to maintain context
4. **API Endpoints**: New endpoints for session management and session-based interactions

### Component Diagram

```
┌─────────────────────────────────────┐
│           MCP Server                │
│                                     │
│  ┌─────────────────────────────┐    │
│  │     Session-Based Tools     │    │
│  │                             │    │
│  │  - session.create           │    │
│  │  - session.feedback         │    │
│  │  - session.process          │    │
│  │  - session.end              │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│  ┌─────────────▼───────────────┐    │
│  │       Session Manager       │    │
│  │                             │    │
│  │  - createSession()          │    │
│  │  - getSession()             │    │
│  │  - updateSession()          │    │
│  │  - endSession()             │    │
│  │  - cleanupExpiredSessions() │    │
│  └─────────────┬───────────────┘    │
│                │                     │
│  ┌─────────────▼───────────────┐    │
│  │       Session Storage       │    │
│  │                             │    │
│  │  - sessions                 │    │
│  └─────────────────────────────┘    │
│                                     │
└─────────────────────────────────────┘
```

## Session Management

### Session Creation

Sessions are created explicitly by calling the `session.create` tool. This returns a session ID that can be used in subsequent calls to session-based tools.

### Session Storage

Sessions are stored in memory with the following structure:

```javascript
{
  sessionId: string,
  createdAt: Date,
  lastAccessedAt: Date,
  history: [
    {
      role: string, // "user" or "assistant"
      content: string,
      timestamp: Date
    }
  ]
}
```

### Session Expiration

Sessions expire after a configurable period of inactivity (default: 30 minutes). Expired sessions are automatically cleaned up by a periodic task.

### Session Termination

Sessions can be explicitly terminated by calling the `session.end` tool. This immediately removes the session and frees up resources.

## API Design

### Session Creation

```
POST /mcp/tools/call
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "session.create",
    "arguments": {}
  }
}
```

Response:

```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "sessionId": "5ae4d22e-9a85-4e6d-80e8-d884addec308"
  }
}
```

### Session-Based Feedback

```
POST /mcp/tools/call
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "session.feedback",
    "arguments": {
      "sessionId": "5ae4d22e-9a85-4e6d-80e8-d884addec308",
      "context": "I am trying to optimize a recursive Fibonacci algorithm.",
      "question": "How can I improve the performance?"
    }
  }
}
```

Response:

```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "feedback": "..."
  }
}
```

### Session-Based Process

```
POST /mcp/tools/call
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "session.process",
    "arguments": {
      "sessionId": "5ae4d22e-9a85-4e6d-80e8-d884addec308",
      "text": "Calculate the 100th Fibonacci number efficiently."
    }
  }
}
```

Response:

```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "response": "..."
  }
}
```

### Session Termination

```
POST /mcp/tools/call
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "session.end",
    "arguments": {
      "sessionId": "5ae4d22e-9a85-4e6d-80e8-d884addec308"
    }
  }
}
```

Response:

```
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "success": true
  }
}
```

## Tool Definitions

The following tools will be added to the AI2AI Feedback MCP server:

### session.create

```json
{
  "name": "session.create",
  "description": "Create a new session for maintaining context across interactions",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

### session.feedback

```json
{
  "name": "session.feedback",
  "description": "Request feedback from a larger model with context from previous interactions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sessionId": {
        "type": "string",
        "description": "ID of the session to use"
      },
      "context": {
        "type": "string",
        "description": "Current context or reasoning"
      },
      "question": {
        "type": "string",
        "description": "Specific question or area of uncertainty"
      }
    },
    "required": ["sessionId", "context", "question"]
  }
}
```

### session.process

```json
{
  "name": "session.process",
  "description": "Process text through a smaller model with feedback from a larger model when needed, maintaining context from previous interactions",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sessionId": {
        "type": "string",
        "description": "ID of the session to use"
      },
      "text": {
        "type": "string",
        "description": "Text to process"
      }
    },
    "required": ["sessionId", "text"]
  }
}
```

### session.end

```json
{
  "name": "session.end",
  "description": "End a session and release its resources",
  "inputSchema": {
    "type": "object",
    "properties": {
      "sessionId": {
        "type": "string",
        "description": "ID of the session to end"
      }
    },
    "required": ["sessionId"]
  }
}
```

## Implementation Plan

1. Create a `SessionManager` class to handle session management
2. Implement session storage
3. Add session-based tools to the MCP server
4. Update the server configuration to enable session support
5. Add periodic cleanup of expired sessions
6. Update the documentation to include session-based tools

## Configuration

The session-based AI2AI Feedback tool can be configured with the following options:

```json
{
  "ai2aiFeedback": {
    "command": "npx",
    "args": [
      "-y",
      "ai2ai-feedback-mcp",
      "--openrouter-api-key=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",
      "--smaller-model=google/gemini-2.0-flash-001",
      "--larger-model=google/gemini-2.0-flash-001",
      "--enable-sessions=true",
      "--session-expiry-minutes=30"
    ]
  }
}
```

## Conclusion

The Session-Based AI2AI Feedback Tool enhances the existing AI2AI Feedback MCP server by adding support for maintaining context across multiple interactions. This allows for more coherent and contextually aware feedback, especially in complex conversations where previous context is important.
