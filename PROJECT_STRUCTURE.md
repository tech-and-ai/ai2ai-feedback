# AI2AI Feedback System: Project Structure

## Directory Structure

```
ai2ai-feedback/
├── api/                      # API Gateway
│   ├── __init__.py
│   ├── routes/               # API routes
│   ├── middleware/           # API middleware
│   └── schemas/              # API request/response schemas
│
├── core/                     # Core components
│   ├── __init__.py
│   ├── task_manager.py       # Task management
│   ├── agent_manager.py      # Agent management
│   ├── model_router.py       # Model routing
│   ├── prompt_manager.py     # Prompt management
│   └── output_processor.py   # Output processing
│
├── models/                   # Data models
│   ├── __init__.py
│   ├── task.py               # Task model
│   ├── agent.py              # Agent model
│   ├── discussion.py         # Discussion model
│   ├── message.py            # Message model
│   └── output.py             # Output model
│
├── services/                 # External services
│   ├── __init__.py
│   ├── research/             # Research service
│   ├── execution/            # Execution environment
│   └── model_providers/      # Model provider integrations
│
├── discussion/               # Discussion framework
│   ├── __init__.py
│   ├── thread.py             # Discussion thread
│   ├── message.py            # Message handling
│   └── consensus.py          # Consensus building
│
├── utils/                    # Utility functions
│   ├── __init__.py
│   ├── logging.py            # Logging utilities
│   ├── validation.py         # Validation utilities
│   └── config.py             # Configuration utilities
│
├── db/                       # Database
│   ├── __init__.py
│   ├── connection.py         # Database connection
│   ├── migrations/           # Database migrations
│   └── repositories/         # Data access repositories
│
├── tests/                    # Tests
│   ├── __init__.py
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   └── fixtures/             # Test fixtures
│
├── config/                   # Configuration
│   ├── __init__.py
│   ├── default.py            # Default configuration
│   ├── development.py        # Development configuration
│   └── production.py         # Production configuration
│
├── scripts/                  # Scripts
│   ├── setup.py              # Setup script
│   ├── migrate.py            # Migration script
│   └── seed.py               # Seed script
│
├── docs/                     # Documentation
│   ├── architecture.md       # Architecture documentation
│   ├── api.md                # API documentation
│   └── deployment.md         # Deployment documentation
│
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore file
├── README.md                 # Project README
├── requirements.txt          # Python dependencies
└── main.py                   # Application entry point
```

## Key Files

### main.py
Entry point for the application. Sets up the application, connects to the database, and starts the API server.

### core/task_manager.py
Manages the lifecycle of tasks, including creation, updating, and querying.

### core/agent_manager.py
Manages agent configuration, availability, and capabilities.

### core/model_router.py
Routes requests to appropriate models based on task requirements.

### core/prompt_manager.py
Generates and manages prompts for different models and tasks.

### core/output_processor.py
Processes, validates, and stores model outputs.

### models/*.py
Data models for the application, including tasks, agents, discussions, messages, and outputs.

### services/research/*.py
Service for gathering information from external sources.

### services/execution/*.py
Service for executing code and commands in a secure environment.

### services/model_providers/*.py
Integrations with model providers like Ollama.

### discussion/*.py
Framework for enabling structured discussions between agents.

### api/routes/*.py
API routes for external systems to interact with the application.

### db/repositories/*.py
Data access repositories for interacting with the database.

### utils/*.py
Utility functions for logging, validation, and configuration.

### tests/*.py
Tests for the application, including unit and integration tests.

### config/*.py
Configuration files for different environments.

### scripts/*.py
Scripts for setting up, migrating, and seeding the application.

### docs/*.md
Documentation for the application, including architecture, API, and deployment.

## Development Workflow

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and update as needed
6. Run database migrations: `python scripts/migrate.py`
7. Seed the database: `python scripts/seed.py`
8. Start the application: `python main.py`

## Testing

Run tests with pytest:

```bash
pytest
```

Run specific test files:

```bash
pytest tests/unit/test_task_manager.py
```

Run tests with coverage:

```bash
pytest --cov=.
```

## Deployment

1. Build the Docker image: `docker build -t ai2ai-feedback .`
2. Run the Docker container: `docker run -p 8000:8000 ai2ai-feedback`

For production deployment, see `docs/deployment.md`.
