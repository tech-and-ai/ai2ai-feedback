# Controller Agent Implementation Plan

## Overview

This document provides a detailed implementation plan for the controller-based architecture in the AI2AI Feedback system. It includes specific code examples, a timeline, and implementation priorities.

## Implementation Timeline

| Phase | Task | Estimated Time | Priority |
|-------|------|----------------|----------|
| 1 | Database Schema Updates | 1 day | High |
| 1 | Controller Agent Core Implementation | 3 days | High |
| 1 | API Enhancements | 1 day | High |
| 2 | Agent Type Framework | 2 days | Medium |
| 2 | Specialized Agent Implementation | 3 days | Medium |
| 2 | Agent Coordination | 2 days | Medium |
| 3 | Dependency Management | 2 days | Medium |
| 3 | Resource Optimization | 2 days | Low |
| 3 | Quality Assurance | 2 days | Low |

Total estimated implementation time: **18 days**

## Phase 1: Core Infrastructure

### 1.1 Database Schema Updates

#### Task Model Extensions

```python
# In app/database.py

class Task(Base):
    __tablename__ = "tasks"
    
    # Existing fields
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String, default="pending")
    created_by = Column(String, nullable=False)
    assigned_to = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    result = Column(Text, nullable=True)
    parent_task_id = Column(String, ForeignKey("tasks.id"), nullable=True)
    priority = Column(Integer, default=5)
    required_skills = Column(JSON, default=list)
    
    # New fields
    project_id = Column(String, nullable=True)  # Group tasks by project
    task_type = Column(String, nullable=True)  # design, development, testing, etc.
    dependencies = Column(JSON, default=list)  # List of task IDs this task depends on
    estimated_effort = Column(Integer, nullable=True)  # Estimated effort in hours
    deadline = Column(DateTime, nullable=True)  # Optional deadline
    progress = Column(Integer, default=0)  # Progress percentage (0-100)
    blockers = Column(JSON, default=list)  # List of issues blocking progress
```

#### Agent Model Extensions

```python
# In app/database.py

class Agent(Base):
    __tablename__ = "agents"
    
    # Existing fields
    agent_id = Column(String, primary_key=True)
    session_id = Column(String, nullable=False)
    agent_index = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    skills = Column(JSON, default=list)
    model = Column(String, nullable=False)
    status = Column(String, default="idle")
    
    # New fields
    agent_type = Column(String, nullable=False, default="worker")  # controller, designer, developer, tester, etc.
    performance_metrics = Column(JSON, default=dict)  # Metrics on agent performance
    current_workload = Column(Integer, default=0)  # Number of active tasks
    max_workload = Column(Integer, default=3)  # Maximum number of concurrent tasks
```

#### Migration Script

```python
# In update_schema.py

async def update_schema():
    """Update the database schema with new fields"""
    async with engine.begin() as conn:
        # Add new columns to tasks table
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS project_id TEXT"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS task_type TEXT"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS dependencies JSON DEFAULT '[]'"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS estimated_effort INTEGER"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS deadline TIMESTAMP"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS progress INTEGER DEFAULT 0"))
        await conn.execute(text("ALTER TABLE tasks ADD COLUMN IF NOT EXISTS blockers JSON DEFAULT '[]'"))
        
        # Add new columns to agents table
        await conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_type TEXT DEFAULT 'worker'"))
        await conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS performance_metrics JSON DEFAULT '{}'"))
        await conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS current_workload INTEGER DEFAULT 0"))
        await conn.execute(text("ALTER TABLE agents ADD COLUMN IF NOT EXISTS max_workload INTEGER DEFAULT 3"))
```

### 1.2 Controller Agent Implementation

#### Controller Agent Class

```python
# In app/controller_agent.py

class ControllerAgent:
    """
    Project Manager agent that allocates and coordinates tasks
    """
    
    def __init__(self, agent_id: str, name: str, model: str):
        self.agent_id = agent_id
        self.name = name
        self.model = model
        self.provider = get_model_provider("ollama", self.model)
        self.status = "idle"
    
    async def start(self):
        """Start the controller agent"""
        self.running = True
        self.status = "running"
        logger.info(f"Controller Agent {self.name} ({self.agent_id}) started")
        
        # Start the project monitoring loop
        asyncio.create_task(self._project_loop())
        return True
    
    async def _project_loop(self):
        """Monitor projects and coordinate tasks"""
        while self.running:
            try:
                # Get database session
                db_gen = get_db()
                db = await anext(db_gen)
                
                # Look for new projects without a plan
                await self._process_new_projects(db)
                
                # Check for completed tasks and handle next steps
                await self._process_completed_tasks(db)
                
                # Check for blocked tasks
                await self._process_blocked_tasks(db)
                
                # Sleep before next check
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in controller loop: {e}")
                await asyncio.sleep(30)
```

#### Project Planning Logic

```python
# In app/controller_agent.py

async def _create_project_plan(self, db, project):
    """Create a plan for a project"""
    # Generate a plan using the AI model
    prompt = f"""
    You are a project manager planning a software development project.
    
    PROJECT REQUIREMENTS:
    {project.description}
    
    Please create a detailed project plan with the following tasks:
    1. Design tasks (architecture, database schema, API design)
    2. Development tasks (backend, frontend, integration)
    3. Testing tasks (unit tests, integration tests)
    4. Documentation tasks
    
    For each task, specify:
    - Task title
    - Task description
    - Required skills
    - Task type (design, development, testing, documentation)
    - Dependencies (which tasks must be completed first)
    - Estimated effort (in hours)
    
    FORMAT YOUR RESPONSE AS JSON:
    {{
      "tasks": [
        {{
          "title": "Task title",
          "description": "Task description",
          "required_skills": ["skill1", "skill2"],
          "task_type": "design|development|testing|documentation",
          "dependencies": [],
          "estimated_effort": 4
        }},
        ...
      ]
    }}
    """
    
    response = await self.provider.generate_completion(
        system_prompt="You are a project management AI that creates detailed project plans.",
        user_prompt=prompt
    )
    
    # Extract the plan
    try:
        plan_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if plan_match:
            plan_json = plan_match.group(1)
            plan = json.loads(plan_json)
            
            # Create tasks based on the plan
            await self._create_tasks_from_plan(db, project, plan)
            
            # Update project status
            project.status = "in_progress"
            await db.commit()
            
            # Add update about plan creation
            await ContextScaffold.add_task_update(
                db,
                project.id,
                self.agent_id,
                f"Created project plan with {len(plan['tasks'])} tasks"
            )
        else:
            logger.error(f"Failed to extract plan from response: {response}")
    except Exception as e:
        logger.error(f"Error creating project plan: {e}")
```

#### Task Assignment Logic

```python
# In app/controller_agent.py

async def _assign_task(self, db, task):
    """Assign a task to an appropriate agent"""
    # Find available agents with matching skills
    query = select(Agent).where(
        Agent.status == "running",
        Agent.agent_type == task.task_type,
        Agent.current_workload < Agent.max_workload,
        or_(
            *[func.json_contains(Agent.skills, f'"{skill}"') for skill in task.required_skills]
        )
    )
    
    result = await db.execute(query)
    agents = result.scalars().all()
    
    if agents:
        # Select the best agent based on skill match and workload
        best_agent = None
        best_score = -1
        
        for agent in agents:
            # Calculate skill match score
            skill_match = sum(1 for skill in task.required_skills if skill in agent.skills)
            skill_score = skill_match / len(task.required_skills) if task.required_skills else 0
            
            # Calculate workload score (lower is better)
            workload_score = 1 - (agent.current_workload / agent.max_workload)
            
            # Combined score
            score = (skill_score * 0.7) + (workload_score * 0.3)
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent:
            # Assign the task
            task.assigned_to = best_agent.agent_id
            task.status = "in_progress"
            
            # Update agent workload
            best_agent.current_workload += 1
            
            await db.commit()
            
            # Add update about assignment
            await ContextScaffold.add_task_update(
                db,
                task.id,
                self.agent_id,
                f"Task assigned to agent {best_agent.name} ({best_agent.agent_id})"
            )
            
            return True
    
    # No suitable agent found
    await ContextScaffold.add_task_update(
        db,
        task.id,
        self.agent_id,
        "No suitable agent found for this task"
    )
    return False
```

### 1.3 API Enhancements

#### Project Creation Endpoint

```python
# In app/main.py

class ProjectCreate(BaseModel):
    title: str
    description: str
    required_skills: List[str] = []
    priority: int = 5

@router.post("/projects")
async def create_project(
    project: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    # Create a project task
    task = Task(
        title=project.title,
        description=project.description,
        status="pending",
        created_by="user",
        task_type="project",
        required_skills=project.required_skills,
        priority=project.priority
    )
    db.add(task)
    await db.commit()
    
    # Find a controller agent
    query = select(Agent).where(
        Agent.agent_type == "controller",
        Agent.status == "running"
    )
    result = await db.execute(query)
    controller = result.scalars().first()
    
    if controller:
        # Assign to controller
        task.assigned_to = controller.agent_id
        task.status = "in_progress"
        await db.commit()
    
    return task
```

## Phase 2: Agent Specialization

### 2.1 Agent Type Framework

```python
# In app/agent_types.py

class BaseAgent:
    """Base class for all agent types"""
    
    def __init__(self, agent_id: str, name: str, role: str, skills: List[str], model: str):
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.skills = set(skills)
        self.model = model
        self.status = "idle"
        self.provider = get_model_provider("ollama", self.model)
        
        # Create workspace
        self.workspace = FileOperations.get_agent_workspace(agent_id, self.name, self.role)
    
    async def start(self):
        """Start the agent"""
        self.running = True
        self.status = "running"
        logger.info(f"Agent {self.name} ({self.agent_id}) started")
        
        # Start the task processing loop
        asyncio.create_task(self._task_loop())
        return True
    
    async def _task_loop(self):
        """Task processing loop"""
        # Implementation will vary by agent type
        pass
    
    async def process_task(self, db: AsyncSession, task_id: str, task_description: str) -> bool:
        """Process a task"""
        # Implementation will vary by agent type
        pass


class DesignerAgent(BaseAgent):
    """Agent specialized in design tasks"""
    
    async def _task_loop(self):
        """Task processing loop for designer agent"""
        # Designer-specific implementation
        pass
    
    async def process_task(self, db: AsyncSession, task_id: str, task_description: str) -> bool:
        """Process a design task"""
        # Designer-specific implementation
        pass


class DeveloperAgent(BaseAgent):
    """Agent specialized in development tasks"""
    
    async def _task_loop(self):
        """Task processing loop for developer agent"""
        # Developer-specific implementation
        pass
    
    async def process_task(self, db: AsyncSession, task_id: str, task_description: str) -> bool:
        """Process a development task"""
        # Developer-specific implementation
        pass


class TesterAgent(BaseAgent):
    """Agent specialized in testing tasks"""
    
    async def _task_loop(self):
        """Task processing loop for tester agent"""
        # Tester-specific implementation
        pass
    
    async def process_task(self, db: AsyncSession, task_id: str, task_description: str) -> bool:
        """Process a testing task"""
        # Tester-specific implementation
        pass
```

## Next Steps

1. Implement the database schema updates
2. Create the controller agent class
3. Update the API to support project creation
4. Test the controller with simple projects
5. Implement the agent type framework
6. Create specialized agent implementations
7. Enhance the system with dependency management
8. Add resource optimization
9. Implement quality assurance mechanisms

## Conclusion

This implementation plan provides a roadmap for enhancing the AI2AI Feedback system with a controller-based architecture. By following this plan, we can create a more efficient, scalable, and autonomous system that can handle complex projects with specialized agents.
