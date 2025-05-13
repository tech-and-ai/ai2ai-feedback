# Kanban Framework Recommendations for AI2AI Job Manager

## Overview

This document provides recommendations for JavaScript frameworks to implement the Kanban-style task management interface outlined in the UI requirements document. The goal is to enhance the existing job manager UI with robust drag-and-drop functionality, improved task visualization, and better agent assignment controls.

## Current Implementation

The current job manager UI implements a basic Kanban-style board with:
- Vertical swimlanes for different task types (design, development, testing, review, documentation)
- A priority override lane for manually prioritized tasks
- Task cards with basic information and controls
- Manual agent assignment via dropdown selectors

The implementation uses vanilla JavaScript with Bootstrap for styling, but lacks proper drag-and-drop functionality between lanes.

## Recommended Frameworks

### 1. Sortable.js (Primary Recommendation)

**Description**: A lightweight (8kb gzipped) standalone JavaScript library for reorderable drag-and-drop lists.

**Benefits**:
- No dependencies and works with standard DOM elements
- Minimal changes required to integrate with existing codebase
- Supports touch devices and modern browsers
- Allows dragging between different lists (swimlanes)
- Customizable animations and drag handles

**Implementation Complexity**: Low

**Example Integration**:
```html
<!-- Add to job_manager.html -->
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
```

```javascript
// Add to job_manager.js
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Sortable on each task list
    const taskLists = document.querySelectorAll('.task-list');
    taskLists.forEach(list => {
        new Sortable(list, {
            group: 'tasks',
            animation: 150,
            ghostClass: 'task-card-ghost',
            chosenClass: 'task-card-chosen',
            dragClass: 'task-card-drag',
            onEnd: function(evt) {
                const taskId = evt.item.dataset.taskId;
                const newStage = evt.to.dataset.stage;
                
                // Handle task moved to priority lane
                if (newStage === 'priority') {
                    prioritizeTask(taskId);
                } 
                // Handle task moved to other lanes
                else {
                    updateTaskType(taskId, newStage);
                }
            }
        });
    });
});
```

### 2. Dragula

**Description**: Simple drag and drop library with minimal footprint.

**Benefits**:
- Easy to use API
- No dependencies
- Handles drag and drop between containers
- Good browser compatibility

**Implementation Complexity**: Low to Medium

**Example Integration**:
```html
<!-- Add to job_manager.html -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.3/dragula.min.js"></script>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/dragula/3.7.3/dragula.min.css">
```

```javascript
// Add to job_manager.js
document.addEventListener('DOMContentLoaded', function() {
    const containers = Array.from(document.querySelectorAll('.task-list'));
    const drake = dragula(containers);
    
    drake.on('drop', function(el, target, source) {
        const taskId = el.dataset.taskId;
        const newStage = target.dataset.stage;
        
        if (newStage === 'priority') {
            prioritizeTask(taskId);
        } else {
            updateTaskType(taskId, newStage);
        }
    });
});
```

### 3. jKanban

**Description**: Pure JavaScript plugin specifically designed for Kanban boards.

**Benefits**:
- Purpose-built for Kanban interfaces
- Includes built-in support for adding, removing, and updating items
- Customizable templates for cards and boards
- Supports drag and drop between columns

**Implementation Complexity**: Medium

**Considerations**:
- Would require restructuring the existing HTML to match jKanban's expected format
- More opinionated about the structure of the Kanban board

### 4. React DnD (If migrating to React)

**Description**: Powerful drag-and-drop library for React applications.

**Benefits**:
- Highly customizable
- Excellent performance with React's virtual DOM
- Well-documented with many examples

**Implementation Complexity**: High

**Considerations**:
- Would require converting the entire frontend to React
- Not recommended unless planning a larger frontend refactoring

## Implementation Plan for Sortable.js

### Step 1: Add Sortable.js to the project

Add the Sortable.js library to the job_manager.html file:

```html
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.0/Sortable.min.js"></script>
```

### Step 2: Initialize Sortable on task lists

Add initialization code to job_manager.js:

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

// Handle task movement between lists
function handleTaskMove(evt) {
    const taskId = evt.item.dataset.taskId;
    const newStage = evt.to.dataset.stage;
    const oldStage = evt.from.dataset.stage;
    
    // Skip if no actual change
    if (newStage === oldStage) return;
    
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

### Step 3: Add updateTaskType function

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
        
        // Refresh UI
        renderUI();
        
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

### Step 4: Add CSS for drag and drop visual feedback

Add CSS classes for drag and drop visual feedback:

```css
/* Add to styles.css */
.task-card-ghost {
    opacity: 0.5;
    background: #c8ebfb;
}

.task-card-chosen {
    box-shadow: 0 0 10px rgba(0, 123, 255, 0.5);
}

.task-card-drag {
    transform: rotate(3deg);
}
```

### Step 5: Call initialization function

Call the initialization function after rendering the UI:

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

## API Endpoints Needed

To support the drag-and-drop functionality, the following API endpoint should be implemented:

```
POST /api/tasks/{task_id}/type
Body: { "task_type": "design|development|testing|review|documentation" }
```

## Conclusion

Sortable.js is the recommended framework for enhancing the Kanban functionality of the AI2AI Job Manager. It provides the necessary drag-and-drop capabilities with minimal changes to the existing codebase, while maintaining good performance and user experience.

The implementation plan outlined above can be executed incrementally, allowing for testing and refinement at each step.
