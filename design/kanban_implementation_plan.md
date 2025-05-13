# Kanban Implementation Plan for AI2AI Job Manager

## Overview

This document outlines the step-by-step implementation plan for enhancing the AI2AI Job Manager with Kanban-style drag-and-drop functionality using Sortable.js. The implementation will follow the requirements specified in the UI requirements document and leverage the existing codebase structure.

## Implementation Phases

### Phase 1: Setup and Integration

#### 1.1 Add Sortable.js Library

Add the Sortable.js library to the job_manager.html file:

```html
<!-- Add before the closing </body> tag -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
```

#### 1.2 Add CSS for Drag-and-Drop Visual Feedback

Add the following CSS classes to styles.css:

```css
/* Drag and drop styling */
.task-card-ghost {
    opacity: 0.5;
    background: #f8f9fa;
    border: 2px dashed #6c757d;
}

.task-card-chosen {
    box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
}

.task-card-drag {
    transform: rotate(2deg);
    cursor: grabbing;
}

.task-list {
    min-height: 100px; /* Ensure empty lists can still be drop targets */
}

.task-list.sortable-drag {
    background-color: rgba(0, 123, 255, 0.1);
}
```

### Phase 2: Core Drag-and-Drop Functionality

#### 2.1 Initialize Sortable on Task Lists

Add the following function to job_manager.js:

```javascript
// Initialize Sortable on task lists
function initializeSortable() {
    const taskLists = document.querySelectorAll('.task-list');
    taskLists.forEach(list => {
        new Sortable(list, {
            group: 'tasks',
            animation: 150,
            ghostClass: 'task-card-ghost',
            chosenClass: 'task-card-chosen',
            dragClass: 'task-card-drag',
            onEnd: handleTaskMove
        });
    });
}
```

#### 2.2 Add Task Movement Handler

Add a function to handle task movement between lists:

```javascript
// Handle task movement between lists
function handleTaskMove(evt) {
    const taskId = evt.item.dataset.taskId;
    const newStage = evt.to.dataset.stage;
    const oldStage = evt.from.dataset.stage;
    
    // Skip if no actual change
    if (newStage === oldStage) return;
    
    console.log(`Task ${taskId} moved from ${oldStage} to ${newStage}`);
    
    // Handle task moved to priority lane
    if (newStage === 'priority') {
        prioritizeTask(taskId);
    } 
    // Handle task moved to other lanes
    else if (['design', 'development', 'testing', 'review', 'documentation'].includes(newStage)) {
        updateTaskType(taskId, newStage);
    }
}
```

#### 2.3 Call Initialization Function

Modify the renderUI function to initialize Sortable after rendering the task cards:

```javascript
// Modify renderUI function
function renderUI() {
    renderProjects();
    renderWorkers();
    renderTaskFlow();
    
    // Initialize Sortable after rendering task cards
    initializeSortable();

    // Show project details if a project is selected
    if (selectedProjectId) {
        const selectedProject = projects.find(p => p.id === selectedProjectId);
        if (selectedProject) {
            showProjectDetails(selectedProject);
        }
    }
}
```

### Phase 3: Backend API Integration

#### 3.1 Add Task Type Update Function

Add a function to update the task type when moved to a different lane:

```javascript
// Update task type when moved to a different lane
async function updateTaskType(taskId, newType) {
    try {
        console.log(`Updating task ${taskId} type to ${newType}`);
        
        // Make API call to update task type
        const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/type`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                task_type: newType
            })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to update task type: ${response.status} ${response.statusText}`);
        }
        
        const updatedTask = await response.json();
        
        // Update task in local data
        const taskIndex = tasks.findIndex(t => t.id === taskId);
        if (taskIndex !== -1) {
            tasks[taskIndex] = updatedTask;
        }
        
        // Show success message
        showSuccess(`Task "${updatedTask.title}" moved to ${newType}`);
    } catch (error) {
        console.error('Error updating task type:', error);
        showError(`Failed to update task type: ${error.message}`);
        
        // Refresh UI to revert the change visually
        renderUI();
    }
}
```

#### 3.2 Add Backend API Endpoint

Add the following endpoint to job_manager_api.py:

```python
@router.post("/api/tasks/{task_id}/type", response_model=Dict[str, Any])
async def update_task_type(task_id: str, type_data: Dict[str, str], db: AsyncSession = Depends(get_db)):
    """
    Update a task's type
    
    Args:
        task_id: Task ID
        type_data: Type data with task_type
        
    Returns:
        Dict[str, Any]: Updated task
    """
    try:
        # Get task
        query = select(Task).where(Task.id == task_id)
        result = await db.execute(query)
        task = result.scalars().first()
        
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        
        # Update task type
        task.task_type = type_data.get("task_type")
        
        # Update timestamp
        task.updated_at = datetime.utcnow()
        
        # Add task update
        task_update = TaskUpdate(
            task_id=task.id,
            agent_id="system",
            content=f"Task type updated to {task.task_type}"
        )
        db.add(task_update)
        
        # Commit changes
        await db.commit()
        await db.refresh(task)
        
        # Convert to dict
        task_dict = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "assigned_to": task.assigned_to,
            "project_id": task.project_id,
            "task_type": task.task_type,
            "progress": task.progress,
            "priority": task.priority
        }
        
        return task_dict
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task type: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating task type: {str(e)}")
```

### Phase 4: Enhanced User Experience

#### 4.1 Add Visual Feedback During Drag

Enhance the task card styling to provide better visual feedback during drag operations:

```css
/* Add to styles.css */
.task-card {
    cursor: grab;
    transition: transform 0.1s, box-shadow 0.1s;
}

.task-card:hover {
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
}

.task-card:active {
    cursor: grabbing;
}

.task-list.sortable-ghost {
    background-color: rgba(0, 123, 255, 0.05);
    border: 2px dashed rgba(0, 123, 255, 0.2);
    border-radius: 5px;
}
```

#### 4.2 Add Animation for Task Movement

Enhance the Sortable initialization with animation options:

```javascript
// Update Sortable initialization
new Sortable(list, {
    group: 'tasks',
    animation: 150,
    easing: "cubic-bezier(1, 0, 0, 1)",
    ghostClass: 'task-card-ghost',
    chosenClass: 'task-card-chosen',
    dragClass: 'task-card-drag',
    onEnd: handleTaskMove,
    // Add delay on mobile to distinguish between tap and drag
    delay: /mobile|tablet|Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ? 100 : 0
});
```

### Phase 5: Testing and Refinement

#### 5.1 Test Cases

1. Drag a task from one lane to another
2. Drag a task to the priority lane
3. Drag a task from the priority lane to a regular lane
4. Test on mobile devices
5. Test with multiple tasks in each lane
6. Test with empty lanes

#### 5.2 Performance Optimization

If performance issues are observed with many tasks, implement the following optimizations:

```javascript
// Add debouncing for UI updates
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

// Debounced version of renderUI
const debouncedRenderUI = debounce(renderUI, 100);

// Use in handleTaskMove
function handleTaskMove(evt) {
    // ... existing code ...
    
    // Use debounced render for better performance
    debouncedRenderUI();
}
```

## Implementation Timeline

1. **Phase 1 (Setup and Integration)**: 1 day
2. **Phase 2 (Core Drag-and-Drop Functionality)**: 2 days
3. **Phase 3 (Backend API Integration)**: 2 days
4. **Phase 4 (Enhanced User Experience)**: 1 day
5. **Phase 5 (Testing and Refinement)**: 2 days

Total estimated time: 8 days

## Conclusion

This implementation plan provides a structured approach to enhancing the AI2AI Job Manager with Kanban-style drag-and-drop functionality. By following these steps, the development team can incrementally add this feature while maintaining compatibility with the existing codebase.

The use of Sortable.js provides a lightweight and flexible solution that meets the requirements specified in the UI requirements document without requiring a complete rewrite of the frontend code.
