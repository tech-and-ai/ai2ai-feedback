# Autonomous Agent Migration Plan

## Overview
This document outlines the plan to decouple the Autonomous Worker from the Lily AI codebase and move it to its own dedicated folder structure. This will make the code more modular and allow the Autonomous Agent to operate independently using Ollama.

## Current Structure
Currently, the Autonomous Worker is integrated within the Lily AI codebase:
- `app/services/autonomous_worker.py` - Main worker implementation
- `app/services/ollama_service.py` - Ollama API integration
- `agent_worker/` - Supporting files and directories

## Target Structure
We will create a new directory structure:
```
/home/admin/projects/ai_autonomous_agent/
├── config/
│   └── config.json
├── logs/
├── inbound/
├── outbound/
├── processed/
├── src/
│   ├── ollama_service.py
│   ├── autonomous_worker.py
│   └── utils/
└── worker_daemon.py
```

## Migration Steps

### 1. Create Directory Structure
```bash
mkdir -p /home/admin/projects/ai_autonomous_agent/{config,logs,inbound,outbound,processed,src/utils}
```

### 2. Copy and Adapt Files
- Copy `app/services/ollama_service.py` to `ai_autonomous_agent/src/ollama_service.py`
  - Update imports and logging configuration
  - Remove any Lily AI-specific code

- Copy `app/services/autonomous_worker.py` to `ai_autonomous_agent/src/autonomous_worker.py`
  - Update imports and paths
  - Remove dependencies on Lily AI codebase
  - Update logging configuration

- Copy `agent_worker/worker_daemon.py` to `ai_autonomous_agent/worker_daemon.py`
  - Update imports and paths
  - Update logging configuration

- Copy `agent_worker/config.json` to `ai_autonomous_agent/config/config.json`
  - Update paths and configuration as needed

- Copy `agent_worker/worker_prompt.md` to `ai_autonomous_agent/config/worker_prompt.md`
  - No changes needed

- Copy `agent_worker/worker_daemon.service` to `ai_autonomous_agent/worker_daemon.service`
  - Update paths to point to the new location

### 3. Update References
- Update all file path references in the code
- Update import statements
- Update logging configuration

### 4. Testing
- Test the Autonomous Agent in its new location
- Verify that it can run independently of the Lily AI codebase

### 5. Cleanup
- Once the migration is complete and tested, remove the Autonomous Worker code from the Lily AI codebase

## Code Changes Required

### ollama_service.py
- Update docstring
- Update logging configuration
- No other significant changes needed

### autonomous_worker.py
- Update imports to use local modules
- Update file paths to use the new directory structure
- Update logging configuration
- Remove any dependencies on Lily AI codebase

### worker_daemon.py
- Update imports to use local modules
- Update file paths to use the new directory structure
- Update logging configuration

## Benefits
- Cleaner separation of concerns
- Reduced coupling between Lily AI and the Autonomous Agent
- Easier maintenance and updates
- Ability to run the Autonomous Agent independently
