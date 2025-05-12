# Session-Based AI2AI Feedback Tool

The Session-Based AI2AI Feedback Tool is an enhancement to the existing AI2AI Feedback MCP server that adds support for maintaining context across multiple interactions. This allows for more coherent and contextually aware feedback, especially in complex conversations where previous context is important.

## Features

- **Session Management**: Create, retrieve, update, and delete sessions
- **Context Preservation**: Maintain conversation history across multiple interactions
- **Session Expiration**: Automatically clean up expired sessions
- **Compatibility**: Maintain compatibility with the existing AI2AI Feedback tools

## Installation

```bash
npm install ai2ai-feedback-mcp
```

## Usage

### Starting the Server

```bash
npx ai2ai-feedback-mcp \
  --openrouter-api-key=YOUR_OPENROUTER_API_KEY \
  --smaller-model=google/gemini-2.0-flash-001 \
  --larger-model=google/gemini-2.0-flash-001 \
  --enable-sessions=true \
  --session-expiry-minutes=30 \
  --cleanup-interval-minutes=5
```

### MCP Client Configuration

```json
{
  "ai2aiFeedback": {
    "command": "npx",
    "args": [
      "-y",
      "ai2ai-feedback-mcp",
      "--openrouter-api-key=YOUR_OPENROUTER_API_KEY",
      "--smaller-model=google/gemini-2.0-flash-001",
      "--larger-model=google/gemini-2.0-flash-001",
      "--enable-sessions=true",
      "--session-expiry-minutes=30",
      "--cleanup-interval-minutes=5"
    ]
  }
}
```

### Using Session-Based Tools

#### Creating a Session

```javascript
const response = await client.callTool('ai2aiFeedback.session.create');
const sessionId = response.sessionId;
```

#### Getting Feedback with Context

```javascript
const feedback1 = await client.callTool('ai2aiFeedback.session.feedback', {
  sessionId,
  context: 'I am trying to optimize a recursive Fibonacci algorithm.',
  question: 'How can I improve the performance?'
});

const feedback2 = await client.callTool('ai2aiFeedback.session.feedback', {
  sessionId,
  context: 'I implemented memoization as suggested.',
  question: 'What is the time complexity now?'
});
```

#### Processing Text with Context

```javascript
const response1 = await client.callTool('ai2aiFeedback.session.process', {
  sessionId,
  text: 'Calculate the 100th Fibonacci number efficiently.'
});

const response2 = await client.callTool('ai2aiFeedback.session.process', {
  sessionId,
  text: 'Now explain the algorithm you used.'
});
```

#### Ending a Session

```javascript
await client.callTool('ai2aiFeedback.session.end', {
  sessionId
});
```

## API Reference

### session.create

Creates a new session for maintaining context across interactions.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {},
  "required": []
}
```

**Response:**
```json
{
  "sessionId": "5ae4d22e-9a85-4e6d-80e8-d884addec308"
}
```

### session.feedback

Requests feedback from a larger model with context from previous interactions.

**Input Schema:**
```json
{
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
```

**Response:**
```json
{
  "feedback": "..."
}
```

### session.process

Processes text through a smaller model with feedback from a larger model when needed, maintaining context from previous interactions.

**Input Schema:**
```json
{
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
```

**Response:**
```json
{
  "response": "..."
}
```

### session.end

Ends a session and releases its resources.

**Input Schema:**
```json
{
  "type": "object",
  "properties": {
    "sessionId": {
      "type": "string",
      "description": "ID of the session to end"
    }
  },
  "required": ["sessionId"]
}
```

**Response:**
```json
{
  "success": true
}
```

## Configuration Options

| Option | Description | Default |
| ------ | ----------- | ------- |
| `--openrouter-api-key` | OpenRouter API key | Required |
| `--smaller-model` | Model to use for initial processing | `google/gemini-2.0-flash-001` |
| `--larger-model` | Model to use for feedback | `google/gemini-2.0-flash-001` |
| `--enable-sessions` | Enable session-based tools | `false` |
| `--session-expiry-minutes` | Number of minutes after which a session expires | `30` |
| `--cleanup-interval-minutes` | Interval in minutes at which to clean up expired sessions | `5` |
| `--port` | Port to run the server on | `8000` |

## License

MIT
