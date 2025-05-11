# AI-to-AI Feedback API

A lightweight FastAPI server that provides AI-to-AI feedback functionality. This API allows one AI model to request feedback from a more powerful model to improve its reasoning and problem-solving capabilities.

## Features

- **Direct Feedback**: Get feedback from a larger model on specific reasoning
- **Session-Based Feedback**: Maintain context across multiple interactions
- **Structured Feedback**: Feedback is structured into sections for easier consumption
- **Multiple Providers**: Support for OpenRouter, Anthropic, OpenAI, and Ollama
- **SQLite Database**: Persistent storage of conversations and feedback
- **Simple API**: RESTful API with clear endpoints and documentation

## Requirements

- Python 3.8+
- FastAPI
- SQLAlchemy
- SQLite
- httpx
- python-dotenv

## Installation

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

4. Create a `.env` file with your configuration:
   ```
   # API Keys
   OPENROUTER_API_KEY=your_openrouter_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   OPENAI_API_KEY=your_openai_api_key

   # Ollama Configuration
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

## Usage

### Starting the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

The server will start on the specified host and port (default: 0.0.0.0:8001).

### API Endpoints

- `GET /`: Basic API information
- `GET /models`: List of available models
- `POST /feedback`: Get direct feedback
- `POST /session/create`: Create a new session
- `POST /session/feedback`: Get feedback with session context
- `POST /session/process`: Process text with potential feedback
- `POST /session/end`: End a session

### Example Usage

#### Direct Feedback

```python
import requests

response = requests.post(
    "http://localhost:8001/feedback",
    json={
        "context": "I am trying to implement a recursive algorithm to calculate Fibonacci numbers. The naive implementation has exponential time complexity because it recalculates the same values multiple times.",
        "question": "What approaches could I use to improve the performance of this algorithm?"
    }
)

print(response.json())
```

#### Session-Based Interaction

```python
import requests

# Create a session
session_response = requests.post(
    "http://localhost:8001/session/create",
    json={}
)
session_id = session_response.json()["session_id"]

# Get feedback with session context
feedback_response = requests.post(
    "http://localhost:8001/session/feedback",
    json={
        "session_id": session_id,
        "context": "I need to implement a sorting algorithm that works well with nearly-sorted data.",
        "question": "What would be the best approach?"
    }
)

print(feedback_response.json())

# End the session when done
requests.post(
    "http://localhost:8001/session/end",
    json={"session_id": session_id}
)
```

## How It Works

1. The primary model (smaller model) processes user input
2. If the model is uncertain, it can request feedback by including "REQUESTING_FEEDBACK" in its response
3. The system detects this marker and extracts the feedback request
4. The feedback request is sent to a larger, more capable model
5. The feedback is structured into sections for easier consumption
6. The feedback is provided back to the primary model
7. The primary model generates an updated response based on the feedback

## Structured Feedback Format

Feedback is structured into the following sections:

- **FEEDBACK_SUMMARY**: Brief summary of the key issue or insight
- **REASONING_ASSESSMENT**: Evaluation of the reasoning approach
- **KNOWLEDGE_GAPS**: Identification of missing information
- **SUGGESTED_APPROACH**: Clear suggestion for how to proceed
- **ADDITIONAL_CONSIDERATIONS**: Other factors that should be considered

## Database Schema

The API uses SQLite with SQLAlchemy for persistent storage:

- **sessions**: Stores session metadata
- **messages**: Stores conversation messages
- **feedback**: Stores structured feedback
- **memories**: Stores agent memories (for context enrichment)
- **code_snippets**: Stores reusable code snippets
- **references**: Stores external references and documentation

## Integration with Other Systems

This API can be integrated with various AI systems to provide on-demand intelligence amplification:

1. **Code Assistants**: Help with algorithm selection, optimization, and debugging
2. **Research Assistants**: Provide feedback on research methodologies and analysis
3. **Content Generation**: Improve quality and accuracy of generated content
4. **Decision Support**: Enhance decision-making by providing alternative perspectives
5. **Education**: Support learning by providing targeted feedback

## License

MIT License

## Acknowledgements

This implementation is based on the AI-to-AI Feedback framework developed for enhancing AI coding assistants.
