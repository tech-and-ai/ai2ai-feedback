# Agent Workspace Structure

This document outlines the structure and organization of agent workspaces in the Autonomous Agent System.

## Overview

Each agent has its own dedicated workspace for executing tasks. The workspace provides:

1. Isolation between agents and tasks
2. Persistent storage for task-related files
3. Python virtual environments for each task
4. Tool access with appropriate permissions
5. Research and output organization

## Base Directory Structure

The base directory for all agent workspaces is `/agent_workspaces/` with the following structure:

```
/agent_workspaces/
├── {agent_id}/
│   ├── global/
│   │   ├── tools/
│   │   └── references/
│   └── tasks/
│       └── {task_id}/
│           ├── venv/
│           ├── src/
│           ├── output/
│           ├── research/
│           └── README.md
```

## Directory Descriptions

### Agent Directory (`/agent_workspaces/{agent_id}/`)

The root directory for a specific agent, containing all its workspaces and resources.

### Global Directory (`/agent_workspaces/{agent_id}/global/`)

Contains resources shared across all tasks for this agent:

- **Tools Directory** (`/global/tools/`): Utility scripts and tools available to the agent
- **References Directory** (`/global/references/`): Reference materials, documentation, and other resources

### Tasks Directory (`/agent_workspaces/{agent_id}/tasks/`)

Contains subdirectories for each task assigned to the agent:

- **Task Directory** (`/tasks/{task_id}/`): Isolated workspace for a specific task

### Task-Specific Directories

Each task directory contains:

- **Virtual Environment** (`/venv/`): Python virtual environment specific to this task
- **Source Directory** (`/src/`): Source code, content, or other primary work products
- **Output Directory** (`/output/`): Generated artifacts, results, and deliverables
- **Research Directory** (`/research/`): Research materials, references, and notes specific to this task
- **README.md**: Task notes, progress updates, and documentation

## Workspace Initialization

When a task is assigned to an agent, the system:

1. Creates the task directory if it doesn't exist
2. Sets up a Python virtual environment
3. Installs basic required packages
4. Creates the directory structure
5. Generates a README.md with task details

Example initialization script:

```python
def initialize_workspace(agent_id, task_id, task_details):
    # Create base directories
    task_dir = f"/agent_workspaces/{agent_id}/tasks/{task_id}"
    os.makedirs(f"{task_dir}/src", exist_ok=True)
    os.makedirs(f"{task_dir}/output", exist_ok=True)
    os.makedirs(f"{task_dir}/research", exist_ok=True)
    
    # Create virtual environment
    subprocess.run(["python", "-m", "venv", f"{task_dir}/venv"])
    
    # Install basic packages
    subprocess.run([
        f"{task_dir}/venv/bin/pip", 
        "install", 
        "requests", 
        "beautifulsoup4", 
        "pandas", 
        "matplotlib"
    ])
    
    # Create README.md
    with open(f"{task_dir}/README.md", "w") as f:
        f.write(f"# {task_details['title']}\n\n")
        f.write(f"## Description\n\n{task_details['description']}\n\n")
        f.write(f"## Status\n\nTask initialized on {datetime.now().isoformat()}\n\n")
        f.write("## Progress\n\n- [ ] Design\n- [ ] Build\n- [ ] Test\n- [ ] Review\n- [ ] Complete\n")
```

## File Management

The system provides APIs for:

1. Listing files in a workspace
2. Retrieving file contents
3. Creating and updating files
4. Executing scripts within the workspace

## Tool Access

Tools are made available to agents through the global tools directory and through API endpoints. Common tools include:

- Terminal command execution
- Python script execution
- Web search utilities
- PDF generation tools
- GitHub integration scripts
- Email sending utilities

## Security Considerations

1. **Isolation**: Each task workspace is isolated to prevent cross-contamination
2. **Permission Control**: Tools and resources have specific permissions
3. **Resource Limits**: CPU, memory, and disk usage are monitored and limited
4. **Execution Sandboxing**: Command execution is sandboxed to prevent system access
5. **Cleanup**: Workspaces are archived or deleted after task completion

## Workspace Lifecycle

1. **Creation**: When a task is assigned to an agent
2. **Active**: During task execution
3. **Archived**: After task completion (read-only)
4. **Deleted**: After a retention period (configurable)

## Example Workspace for an Essay Task

For a task like "Write an essay on Ancient Rome for an 11-year-old":

```
/agent_workspaces/agent-123/tasks/task-456/
├── venv/                           # Python environment
├── src/
│   ├── essay_draft.md              # Initial draft
│   ├── essay_final.md              # Final version
│   └── images/                     # Images for the essay
├── output/
│   ├── ancient_rome_essay.pdf      # Generated PDF
│   └── ancient_rome_essay.docx     # Word document version
├── research/
│   ├── roman_empire_notes.md       # Research notes
│   ├── roman_daily_life.md         # Topic-specific research
│   ├── child_friendly_terms.md     # Age-appropriate language notes
│   └── sources.md                  # List of sources
└── README.md                       # Task tracking and notes
```

## Example Workspace for a Coding Task

For a task like "Create a simple weather dashboard app":

```
/agent_workspaces/agent-123/tasks/task-789/
├── venv/                           # Python environment with required packages
├── src/
│   ├── app.py                      # Main application code
│   ├── weather_api.py              # API integration
│   ├── static/                     # Static assets
│   └── templates/                  # HTML templates
├── output/
│   ├── weather_dashboard.zip       # Packaged application
│   └── screenshots/                # Application screenshots
├── research/
│   ├── weather_apis.md             # API research
│   ├── dashboard_designs.md        # UI design research
│   └── performance_notes.md        # Performance considerations
└── README.md                       # Task tracking and notes
```

This workspace structure provides a consistent, organized environment for agents to work on tasks while maintaining isolation, security, and proper resource management.
