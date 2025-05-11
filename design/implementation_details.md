# Implementation Details: AI-to-AI Feedback System Fixes

This document explains the technical details of the fixes and improvements made to the AI-to-AI Feedback System.

## 1. Background Task Handling Fix

### Problem

The original implementation of the `start_agent_loop` function in `multi_agent.py` was awaiting the agent task loop, which blocked the execution of subsequent agent loops:

```python
async def start_agent_loop(agent_id: str, agent_model: str, agent_role: str) -> None:
    # Create task for agent loop
    task = asyncio.create_task(agent_task_loop(agent_id, agent_model, agent_role))
    
    # Store task
    agent_loops[agent_id] = task
    
    # Wait for task to complete - THIS WAS BLOCKING
    try:
        await task
    except asyncio.CancelledError:
        logger.info(f"Agent loop for {agent_id} was cancelled")
    except Exception as e:
        logger.error(f"Agent loop for {agent_id} failed: {e}")
    finally:
        # Remove task from dictionary
        if agent_id in agent_loops:
            del agent_loops[agent_id]
```

When using FastAPI's `BackgroundTasks`, each task is executed sequentially. Since the agent loops are designed to run indefinitely, the first agent loop would block all subsequent ones from starting.

### Solution

We modified the `start_agent_loop` function to use a callback instead of awaiting the task:

```python
async def start_agent_loop(agent_id: str, agent_model: str, agent_role: str) -> None:
    # Create task for agent loop
    task = asyncio.create_task(agent_task_loop(agent_id, agent_model, agent_role))
    
    # Store task
    agent_loops[agent_id] = task
    
    # Set up a callback for when the task completes
    def task_done_callback(t):
        try:
            # Handle any exceptions
            if t.exception():
                logger.error(f"Agent loop for {agent_id} failed: {t.exception()}")
            else:
                logger.info(f"Agent loop for {agent_id} completed normally")
        except asyncio.CancelledError:
            logger.info(f"Agent loop for {agent_id} was cancelled")
        finally:
            # Remove task from dictionary
            agent_loops.pop(agent_id, None)
    
    # Add the callback
    task.add_done_callback(task_done_callback)
```

This approach allows the function to return immediately after starting the agent loop, without blocking subsequent agent loops from starting.

## 2. Agent Management Endpoints

### Problem

The original implementation lacked endpoints for managing agent loops, making it difficult to:
- Check which agent loops are running
- Restart failed agent loops
- Start all agent loops for a session

### Solution

We added several new endpoints to the `multi_agent.py` module:

1. **Get Session Agents**: Retrieves information about all agents in a session, including whether they're active:

```python
@router.get("/agents/{session_id}")
async def get_session_agents(session_id: str, db: AsyncSession = Depends(get_db)):
    # Implementation details...
    return {
        "session_id": session_id,
        "agents": formatted_agents
    }
```

2. **Restart Agent**: Restarts a specific agent's task loop:

```python
@router.post("/agents/{session_id}/restart/{agent_index}")
async def restart_agent(session_id: str, agent_index: int, db: AsyncSession = Depends(get_db)):
    # Implementation details...
    return {"success": True, "message": f"Agent {agent_index} restarted"}
```

3. **Start All Agents**: Starts all agent loops for a session:

```python
@router.post("/agents/{session_id}/start_all")
async def start_all_agents(session_id: str, db: AsyncSession = Depends(get_db)):
    # Implementation details...
    return {
        "success": True, 
        "message": f"Started {started_count} agent loops for session {session_id}"
    }
```

These endpoints provide the necessary tools for managing agent loops and ensuring they're running correctly.

## 3. Task Delegation Improvements

### Problem

The original implementation required agents to know the exact agent IDs to delegate tasks, which was not user-friendly and error-prone.

### Solution

We added a helper function to resolve agent names or roles to agent IDs:

```python
@staticmethod
async def get_agent_by_name_or_role(db: AsyncSession, session_id: str, name_or_role: str) -> Optional[str]:
    """Get agent ID by name or role"""
    try:
        # Try exact match on name or role
        stmt = select(Agent).where(
            Agent.session_id == session_id,
            (Agent.name == name_or_role) | (Agent.role == name_or_role)
        )
        result = await db.execute(stmt)
        agent = result.scalars().first()
        
        if agent:
            return f"{session_id}_{agent.agent_index}"
        
        # Try partial match if exact match fails
        stmt = select(Agent).where(
            Agent.session_id == session_id,
            (Agent.name.ilike(f"%{name_or_role}%")) | (Agent.role.ilike(f"%{name_or_role}%"))
        )
        result = await db.execute(stmt)
        agent = result.scalars().first()
        
        if agent:
            return f"{session_id}_{agent.agent_index}"
            
        return None
    except Exception as e:
        logger.error(f"Error finding agent by name or role: {e}")
        return None
```

We then modified the `process_agent_response` function to use this helper function when processing delegation requests:

```python
# Check if delegate_to is a name/role or an agent ID
delegatee_id = delegation_data["delegate_to"]
if not delegatee_id.startswith(f"{session_id}_"):
    # Try to resolve by name or role
    resolved_id = await TaskManager.get_agent_by_name_or_role(
        db, 
        session_id, 
        delegation_data["delegate_to"]
    )
    
    if resolved_id:
        delegatee_id = resolved_id
        logger.info(f"Resolved '{delegation_data['delegate_to']}' to agent ID: {delegatee_id}")
    else:
        logger.error(f"Could not resolve agent '{delegation_data['delegate_to']}' to a valid agent ID")
        # Add update about the error
        await ContextScaffold.add_task_update(
            db,
            task_id,
            agent_id,
            f"Failed to delegate task: Could not find agent '{delegation_data['delegate_to']}'"
        )
        return
```

We also updated the agent task prompts to make it clear that agents can delegate tasks by name or role:

```python
To delegate a subtask:
```delegate
{{
  "task": {{
    "title": "Subtask title",
    "description": "Detailed subtask description"
  }},
  "delegate_to": "Agent name, role, or ID"
}}
```
```

## 4. Response Retrieval Endpoint

### Problem

The original implementation lacked an endpoint for retrieving completed task responses, making it difficult to see the results of agent work.

### Solution

We added a new endpoint to retrieve all completed task responses for a session:

```python
@router.get("/responses/{session_id}")
async def get_session_responses(session_id: str, db: AsyncSession = Depends(get_db)):
    # Implementation details...
    return {
        "session_id": session_id,
        "responses": responses
    }
```

This endpoint retrieves all completed tasks for a session, along with their results and information about the agent that completed them.

## 5. Error Handling Improvements

### Problem

The original implementation had minimal error handling, particularly for task delegation and agent loop failures.

### Solution

We improved error handling in several areas:

1. **Task Delegation**: Added error handling for invalid agent names/roles:

```python
if not resolved_id:
    logger.error(f"Could not resolve agent '{delegation_data['delegate_to']}' to a valid agent ID")
    # Add update about the error
    await ContextScaffold.add_task_update(
        db,
        task_id,
        agent_id,
        f"Failed to delegate task: Could not find agent '{delegation_data['delegate_to']}'"
    )
    return
```

2. **Agent Loop Callbacks**: Enhanced error handling in the agent loop callback:

```python
def task_done_callback(t):
    try:
        # Handle any exceptions
        if t.exception():
            logger.error(f"Agent loop for {agent_id} failed: {t.exception()}")
        else:
            logger.info(f"Agent loop for {agent_id} completed normally")
    except asyncio.CancelledError:
        logger.info(f"Agent loop for {agent_id} was cancelled")
    finally:
        # Remove task from dictionary
        agent_loops.pop(agent_id, None)
```

These improvements make the system more robust and provide better feedback when errors occur.
