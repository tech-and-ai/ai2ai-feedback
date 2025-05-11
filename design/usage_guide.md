# AI-to-AI Feedback System Usage Guide

This guide explains how to use the AI-to-AI Feedback System for creating multi-agent discussions and delegating tasks between AI agents.

## Getting Started

### Prerequisites

- Python 3.8+
- API keys for at least one model provider (OpenRouter, Anthropic, or OpenAI)
- For local models: Ollama running on your machine

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/tech-and-ai/ai2ai-feedback.git
   cd ai2ai-feedback
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure your `.env` file with API keys and settings:
   ```
   # API Keys
   OPENROUTER_API_KEY=your_openrouter_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   OPENAI_API_KEY=your_openai_api_key

   # Ollama Configuration (for local models)
   OLLAMA_ENDPOINT=http://localhost:11434

   # Default Models
   DEFAULT_PROVIDER=openrouter
   DEFAULT_MODEL=anthropic/claude-3-opus-20240229

   # Database Configuration
   DATABASE_URL=sqlite:///./ai2ai_feedback.db

   # Server Configuration
   HOST=0.0.0.0
   PORT=8001
   DEBUG=False
   ```

5. Start the server:
   ```bash
   python run.py
   ```

6. Access the API documentation at `http://localhost:8001/docs`

## Creating a Multi-Agent Session

You can create a multi-agent session with any number of agents (up to 10) using the API:

```bash
curl -X POST http://localhost:8001/multi-agent/create \
  -H "Content-Type: application/json" \
  -d '{
    "num_agents": 5,
    "title": "Problem Solving Team",
    "system_prompt": "You are part of a collaborative problem-solving team. Work together to solve complex problems.",
    "tags": ["problem-solving", "collaboration"],
    "agent_names": ["Researcher", "Analyst", "Engineer", "Critic", "Coordinator"],
    "agent_roles": ["Research information", "Analyze data", "Implement solutions", "Critique ideas", "Coordinate team"],
    "agent_models": ["anthropic/claude-3-opus-20240229", "google/gemini-2.0-flash-001", "anthropic/claude-3-opus-20240229", "google/gemini-2.0-flash-001", "anthropic/claude-3-opus-20240229"]
  }'
```

This will return a session ID that you'll use for subsequent interactions:

```json
{
  "session_id": "1d8cb5e1-6f77-4a03-8929-12a987dc92a5"
}
```

## Sending Messages to Agents

To send a message to all agents in a session:

```bash
curl -X POST http://localhost:8001/multi-agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "1d8cb5e1-6f77-4a03-8929-12a987dc92a5",
    "message": "How can we design a system to reduce plastic waste in urban environments?"
  }'
```

To target specific agents, include their indices:

```bash
curl -X POST http://localhost:8001/multi-agent/message \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "1d8cb5e1-6f77-4a03-8929-12a987dc92a5",
    "message": "What are the technical challenges of implementing this solution?",
    "target_agents": [2, 3]
  }'
```

## Managing Agent Loops

If you notice that some agent loops aren't running, you can start or restart them:

### Start All Agent Loops

```bash
curl -X POST http://localhost:8001/multi-agent/agents/1d8cb5e1-6f77-4a03-8929-12a987dc92a5/start_all
```

### Restart a Specific Agent Loop

```bash
curl -X POST http://localhost:8001/multi-agent/agents/1d8cb5e1-6f77-4a03-8929-12a987dc92a5/restart/2
```

## Checking Agent Status

To check the status of all agents in a session:

```bash
curl -X GET http://localhost:8001/multi-agent/agents/1d8cb5e1-6f77-4a03-8929-12a987dc92a5
```

This will return information about each agent, including whether they're active:

```json
{
  "session_id": "1d8cb5e1-6f77-4a03-8929-12a987dc92a5",
  "agents": [
    {
      "index": 0,
      "name": "Researcher",
      "role": "Research information",
      "model": "anthropic/claude-3-opus-20240229",
      "is_active": true
    },
    ...
  ]
}
```

## Viewing Tasks

To see all tasks in a session:

```bash
curl -X GET http://localhost:8001/multi-agent/tasks/1d8cb5e1-6f77-4a03-8929-12a987dc92a5
```

## Retrieving Agent Responses

To get all completed task responses:

```bash
curl -X GET http://localhost:8001/multi-agent/responses/1d8cb5e1-6f77-4a03-8929-12a987dc92a5
```

This will return all completed tasks with their results:

```json
{
  "session_id": "1d8cb5e1-6f77-4a03-8929-12a987dc92a5",
  "responses": [
    {
      "task_id": "aeeb7579-2480-409c-a573-83dc9fd4f1d2",
      "title": "Process message: How can we design a system to reduce plastic...",
      "description": "How can we design a system to reduce plastic waste in urban environments?",
      "result": "To design a system for reducing plastic waste in urban environments, we need a multi-faceted approach...",
      "completed_at": "2025-05-11T21:35:42.123456",
      "agent": {
        "index": 0,
        "name": "Researcher",
        "role": "Research information",
        "model": "anthropic/claude-3-opus-20240229"
      }
    },
    ...
  ]
}
```

## Task Delegation Between Agents

Agents can delegate tasks to each other automatically. When an agent processes a task, it can create subtasks and assign them to other agents by name, role, or ID.

For example, if the Researcher agent finds information that needs analysis, it might delegate a subtask to the Analyst agent:

```
To delegate a subtask:
```delegate
{
  "task": {
    "title": "Analyze plastic waste data",
    "description": "Analyze the data I found on plastic waste generation in urban areas and identify key trends."
  },
  "delegate_to": "Analyst"
}
```
```

The system will:
1. Resolve "Analyst" to the correct agent ID
2. Create a new task with the specified title and description
3. Assign it to the Analyst agent
4. Add a context entry to track the delegation

## Getting Direct Feedback

You can also get direct feedback from a larger model:

```bash
curl -X POST http://localhost:8001/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "context": "I'm designing a system to reduce plastic waste in urban environments by implementing smart bins that sort recyclables automatically.",
    "question": "What are potential issues with this approach that I might be overlooking?"
  }'
```

## Web Interface

A simple web interface is available at:

- Multi-agent client: `http://localhost:8001/multi-agent-client`
- Streaming client: `http://localhost:8001/`

## Troubleshooting

### Agent Loops Not Starting

If agent loops aren't starting:

1. Check the server logs for errors
2. Ensure your API keys are valid
3. Try restarting specific agent loops using the `/agents/{session_id}/restart/{agent_index}` endpoint
4. Restart all agent loops with `/agents/{session_id}/start_all`

### Task Delegation Issues

If task delegation isn't working:

1. Ensure the agent name or role is correct
2. Check that the session ID is valid
3. Verify that the target agent's loop is running

### Model API Errors

If you're seeing model API errors:

1. Check your API keys in the `.env` file
2. Ensure you have sufficient credits/quota with the provider
3. Try switching to a different model or provider
