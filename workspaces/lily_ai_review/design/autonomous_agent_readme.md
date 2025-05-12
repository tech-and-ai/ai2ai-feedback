# AI Autonomous Agent

## Overview
The AI Autonomous Agent is a standalone tool that uses Ollama to analyze code, generate documentation, and provide insights about codebases. It works by monitoring an inbound directory for files to process, analyzing them using AI models, and storing the results in an outbound directory.

## Features
- Code analysis and documentation generation
- Support for multiple programming languages
- Integration with Ollama for local AI processing
- Configurable processing rules
- Daemon mode for continuous operation

## Directory Structure
```
/home/admin/projects/ai_autonomous_agent/
├── config/
│   ├── config.json         # Configuration settings
│   └── worker_prompt.md    # Prompt templates for AI
├── logs/                   # Log files
├── inbound/                # Files to be processed
├── outbound/               # Processed results
├── processed/              # Archive of processed files
├── src/
│   ├── ollama_service.py   # Ollama API integration
│   ├── autonomous_worker.py # Main worker implementation
│   └── utils/              # Utility functions
└── worker_daemon.py        # Daemon process
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Ollama installed and running locally (or accessible via network)

### Setup
1. Clone the repository
2. Install dependencies:
   ```bash
   pip install requests
   ```
3. Configure Ollama:
   - Ensure Ollama is running
   - Download required models:
     ```bash
     ollama pull gemma3:4b
     ```

## Configuration
Edit `config/config.json` to customize the behavior:

```json
{
  "include_patterns": ["*.py", "*.js", "*.ts", "*.html", "*.css"],
  "exclude_patterns": ["node_modules", "__pycache__", "*.pyc", "*.map"],
  "ai_providers": {
    "ollama": {
      "enabled": true,
      "base_url": "http://localhost:11434",
      "model": "gemma3:4b",
      "temperature": 0.2,
      "max_tokens": 4000
    }
  },
  "default_provider": "ollama",
  "polling_interval": 60,
  "max_file_size_mb": 1
}
```

## Usage

### Manual Mode
Run the worker manually:
```bash
python worker_daemon.py --once
```

### Daemon Mode
Run as a background service:
```bash
python worker_daemon.py
```

### Systemd Service
Install as a systemd service:
```bash
sudo cp worker_daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable worker_daemon
sudo systemctl start worker_daemon
```

## Processing Files
1. Place files to be processed in the `inbound` directory
2. The agent will automatically process them and place results in the `outbound` directory
3. Original files will be moved to the `processed` directory

## Logs
Logs are stored in the `logs` directory:
- `autonomous_worker.log` - Main worker logs
- `ollama_service.log` - Ollama API interaction logs
- `worker_daemon.log` - Daemon process logs

## Extending
- Add new language support by updating the code analysis methods
- Customize prompts in `worker_prompt.md`
- Add new AI providers by implementing additional service classes
