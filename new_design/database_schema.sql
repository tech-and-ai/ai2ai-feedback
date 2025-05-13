-- Database Schema for Autonomous Agent System

-- Agents Table
CREATE TABLE IF NOT EXISTS agents (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    model TEXT NOT NULL,
    endpoint TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('available', 'busy', 'offline')),
    min_complexity INTEGER NOT NULL CHECK (min_complexity >= 1 AND min_complexity <= 10),
    max_complexity INTEGER NOT NULL CHECK (max_complexity >= 1 AND max_complexity <= 10),
    workspace_path TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (min_complexity <= max_complexity)
);

-- Tasks Table
CREATE TABLE IF NOT EXISTS tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    complexity INTEGER NOT NULL CHECK (complexity >= 1 AND complexity <= 10),
    status TEXT NOT NULL CHECK (status IN ('not_started', 'design', 'build', 'test', 'review', 'complete')),
    stage_progress INTEGER NOT NULL DEFAULT 0 CHECK (stage_progress >= 0 AND stage_progress <= 100),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    assigned_agent_id TEXT,
    result_path TEXT,
    priority INTEGER NOT NULL DEFAULT 5 CHECK (priority >= 1 AND priority <= 10),
    FOREIGN KEY (assigned_agent_id) REFERENCES agents(id)
);

-- Task Updates Table
CREATE TABLE IF NOT EXISTS task_updates (
    id TEXT PRIMARY KEY,
    task_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    update_type TEXT NOT NULL CHECK (update_type IN ('status_change', 'progress_update', 'note')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Agent Workspaces Table
CREATE TABLE IF NOT EXISTS agent_workspaces (
    id TEXT PRIMARY KEY,
    agent_id TEXT NOT NULL,
    task_id TEXT NOT NULL,
    workspace_path TEXT NOT NULL,
    venv_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    UNIQUE (agent_id, task_id)
);

-- Sessions Table (for human-AI discussions)
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    system_prompt TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status TEXT NOT NULL CHECK (status IN ('active', 'archived', 'deleted')) DEFAULT 'active',
    tags TEXT
);

-- Messages Table (for human-AI discussions)
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('system', 'user', 'assistant', 'tool')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Tools Table
CREATE TABLE IF NOT EXISTS tools (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('terminal', 'python', 'search', 'github', 'email', 'file', 'other')),
    config TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Agent Tools Table (many-to-many relationship)
CREATE TABLE IF NOT EXISTS agent_tools (
    agent_id TEXT NOT NULL,
    tool_id TEXT NOT NULL,
    permissions TEXT NOT NULL DEFAULT 'read',
    PRIMARY KEY (agent_id, tool_id),
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (tool_id) REFERENCES tools(id)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_agent ON tasks(assigned_agent_id);
CREATE INDEX IF NOT EXISTS idx_task_updates_task_id ON task_updates(task_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_agents_status ON agents(status);
CREATE INDEX IF NOT EXISTS idx_agents_complexity ON agents(min_complexity, max_complexity);

-- Create views for common queries
CREATE VIEW IF NOT EXISTS available_agents AS
SELECT * FROM agents WHERE status = 'available';

CREATE VIEW IF NOT EXISTS active_tasks AS
SELECT * FROM tasks WHERE status != 'complete';

CREATE VIEW IF NOT EXISTS agent_task_summary AS
SELECT 
    a.id AS agent_id, 
    a.name AS agent_name,
    a.model,
    a.status,
    COUNT(t.id) AS total_tasks,
    SUM(CASE WHEN t.status = 'complete' THEN 1 ELSE 0 END) AS completed_tasks
FROM 
    agents a
LEFT JOIN 
    tasks t ON a.id = t.assigned_agent_id
GROUP BY 
    a.id;
