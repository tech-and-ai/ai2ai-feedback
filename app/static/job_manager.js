// Global variables
let selectedProjectId = null;
let workers = [];
let projects = [];
let tasks = [];

// API configuration
const API_BASE_URL = 'http://localhost:8005'; // Update this to match your server port

// Show error message
function showError(message) {
    console.error(message);
    const errorDiv = document.createElement('div');
    errorDiv.className = 'alert alert-danger alert-dismissible fade show';
    errorDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.getElementById('alerts-container').appendChild(errorDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        errorDiv.classList.remove('show');
        setTimeout(() => errorDiv.remove(), 500);
    }, 5000);
}

// Show success message
function showSuccess(message) {
    console.log(message);
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show';
    successDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.getElementById('alerts-container').appendChild(successDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        successDiv.classList.remove('show');
        setTimeout(() => successDiv.remove(), 500);
    }, 5000);
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set up event listeners
    document.getElementById('project-form').addEventListener('submit', createProject);
    document.getElementById('detail-close-btn').addEventListener('click', closeProjectDetails);
    document.getElementById('manage-agents-btn').addEventListener('click', openAgentManagementModal);

    // Start data polling
    fetchInitialData();

    // Set up agent management
    setupAgentManagement();

    // Set up polling for updates
    setInterval(updateData, 5000);
});

// Fetch initial data
async function fetchInitialData() {
    try {
        console.log('Fetching initial data...');

        console.log('Fetching workers...');
        const workersResult = await fetchWorkers();
        console.log('Workers fetched:', workersResult);

        console.log('Fetching projects...');
        const projectsResult = await fetchProjects();
        console.log('Projects fetched:', projectsResult);

        console.log('Fetching tasks...');
        const tasksResult = await fetchAllTasks();
        console.log('Tasks fetched:', tasksResult);

        console.log('Rendering UI...');
        renderUI();
        console.log('UI rendered');
    } catch (error) {
        console.error('Error fetching initial data:', error);
        showError('Failed to load initial data. Please refresh the page.');
    }
}

// Update data periodically
async function updateData() {
    try {
        await fetchWorkers();
        await fetchProjects();
        await fetchAllTasks();
        renderUI();
    } catch (error) {
        console.error('Error updating data:', error);
    }
}

// Fetch workers from the API
async function fetchWorkers() {
    try {
        // Get all agents from the database
        const response = await fetch(`${API_BASE_URL}/api/agents`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            console.error(`Failed to fetch workers. Status: ${response.status}, StatusText: ${response.statusText}`);
            throw new Error('Failed to fetch workers');
        }

        // Filter to only include worker agents
        const allAgents = await response.json();
        workers = allAgents.filter(agent => agent.agent_type === 'worker');
        return workers;
    } catch (error) {
        console.error('Error fetching workers:', error);
        showError('Failed to load workers. Please try refreshing the page.');
        return [];
    }
}

// Fetch projects from the API
async function fetchProjects() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/projects`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            console.error(`Failed to fetch projects. Status: ${response.status}, StatusText: ${response.statusText}`);
            throw new Error('Failed to fetch projects');
        }

        projects = await response.json();
        return projects;
    } catch (error) {
        console.error('Error fetching projects:', error);
        showError('Failed to load projects. Please try refreshing the page.');
        return [];
    }
}

// Fetch all tasks for all projects
async function fetchAllTasks() {
    tasks = [];
    try {
        for (const project of projects) {
            const projectTasks = await fetchTasksForProject(project.id);
            tasks = tasks.concat(projectTasks);
        }
        return tasks;
    } catch (error) {
        console.error('Error fetching all tasks:', error);
        return [];
    }
}

// Fetch tasks for a specific project
async function fetchTasksForProject(projectId) {
    try {
        // Use the correct port for the API server
        const apiBaseUrl = 'http://localhost:8003'; // Update this to match your server port

        // Add proper headers to handle CORS
        const response = await fetch(`${apiBaseUrl}/api/projects/${projectId}/tasks`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            // Don't use credentials for cross-origin requests unless the server is configured for it
            // credentials: 'same-origin'
        });

        if (!response.ok) {
            // Log more detailed error information
            console.error(`Failed to fetch tasks for project ${projectId}. Status: ${response.status}, StatusText: ${response.statusText}`);

            // Try to get error details from response
            try {
                const errorData = await response.json();
                console.error('Error details:', errorData);
            } catch (e) {
                // If we can't parse the error as JSON, just log the raw text
                const errorText = await response.text();
                console.error('Error response:', errorText);
            }

            throw new Error(`Failed to fetch tasks for project ${projectId}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`Error fetching tasks for project ${projectId}:`, error);
        // Return empty array but show a notification to the user
        showError(`Failed to load tasks for project ${projectId}. Please try refreshing the page.`);
        return [];
    }
}

// Create a new project
async function createProject(event) {
    event.preventDefault();

    const title = document.getElementById('title').value;
    const description = document.getElementById('description').value;
    const skills = document.getElementById('skills').value.split(',').map(skill => skill.trim());
    const priority = parseInt(document.getElementById('priority').value);

    const projectData = {
        title,
        description,
        required_skills: skills,
        priority
    };

    try {
        console.log('Creating project with data:', projectData);

        // Use the projects API directly instead of our API
        const response = await fetch(`${API_BASE_URL}/projects`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(projectData)
        });

        if (!response.ok) {
            throw new Error(`Failed to create project: ${response.status} ${response.statusText}`);
        }

        const newProject = await response.json();
        console.log('Project created:', newProject);

        // Add the new project to the list
        projects.push(newProject);

        // Reset form
        document.getElementById('project-form').reset();

        // Update UI
        renderUI();

        // Show success message
        showSuccess(`Project "${title}" created successfully!`);
    } catch (error) {
        console.error('Error creating project:', error);
        showError(`Failed to create project: ${error.message}`);
    }
}

// Render the UI with current data
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

// Initialize Sortable on task lists
function initializeSortable() {
    const taskLists = document.querySelectorAll('.task-list');
    taskLists.forEach(list => {
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
    });
    console.log('Sortable initialized on task lists');
}

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

// Render the projects list
function renderProjects() {
    const projectsList = document.getElementById('projects-list');
    projectsList.innerHTML = '';

    projects.forEach(project => {
        const projectItem = document.createElement('div');
        projectItem.className = `list-group-item project-item ${project.id === selectedProjectId ? 'active' : ''}`;
        projectItem.dataset.projectId = project.id;

        // Create project title and status badge
        const projectTitle = document.createElement('a');
        projectTitle.href = '#';
        projectTitle.className = 'd-block mb-1';
        projectTitle.textContent = project.title;

        const statusBadge = document.createElement('span');
        statusBadge.className = `badge ${getStatusBadgeClass(project.status)} float-end`;
        statusBadge.textContent = project.status;

        projectTitle.appendChild(statusBadge);

        // Create delete all tasks button
        const deleteAllBtn = document.createElement('button');
        deleteAllBtn.className = 'btn btn-sm btn-outline-danger mt-1';
        deleteAllBtn.innerHTML = '<i class="bi bi-trash"></i> Delete All Tasks';
        deleteAllBtn.dataset.projectId = project.id;

        // Add elements to project item
        projectItem.appendChild(projectTitle);
        projectItem.appendChild(deleteAllBtn);

        // Add event listeners
        projectTitle.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            selectedProjectId = project.id;
            showProjectDetails(project);
            renderUI();
        });

        deleteAllBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (confirm(`Are you sure you want to delete ALL tasks for project "${project.title}"?`)) {
                deleteAllProjectTasks(project.id);
            }
        });

        projectsList.appendChild(projectItem);
    });
}

// Show project details
function showProjectDetails(project) {
    const detailPanel = document.getElementById('project-detail-panel');

    // Set project details
    document.getElementById('detail-project-title').textContent = project.title;
    document.getElementById('detail-project-description').textContent = project.description;

    const statusBadge = document.getElementById('detail-project-status');
    statusBadge.className = `badge ${getStatusBadgeClass(project.status)}`;
    statusBadge.textContent = project.status;

    document.getElementById('detail-project-created').textContent = new Date(project.created_at).toLocaleString();

    // Set skills
    const skillsContainer = document.getElementById('detail-project-skills');
    skillsContainer.innerHTML = '';
    if (project.required_skills && project.required_skills.length > 0) {
        project.required_skills.forEach(skill => {
            const skillBadge = document.createElement('span');
            skillBadge.className = 'skill-badge';
            skillBadge.textContent = skill;
            skillsContainer.appendChild(skillBadge);
        });
    } else {
        skillsContainer.innerHTML = '<em>No specific skills required</em>';
    }

    document.getElementById('detail-project-priority').textContent = project.priority;

    // Get tasks for this project
    const projectTasks = tasks.filter(task => task.project_id === project.id);

    // Get agents assigned to this project's tasks
    const agentsContainer = document.getElementById('detail-project-agents');
    agentsContainer.innerHTML = '';

    // Get unique agents working on this project
    const assignedAgentIds = [...new Set(projectTasks.map(task => task.assigned_to).filter(id => id))];

    if (assignedAgentIds.length > 0) {
        assignedAgentIds.forEach(agentId => {
            const agent = workers.find(w => w.agent_id === agentId);
            if (!agent) return;

            // Get tasks assigned to this agent for this project
            const agentTasks = projectTasks.filter(task => task.assigned_to === agentId);

            const agentCard = document.createElement('div');
            agentCard.className = 'agent-detail-card';

            // Determine agent status
            const isWorking = agentTasks.some(task => task.status === 'in_progress');
            const statusClass = isWorking ? 'bg-success' : 'bg-secondary';
            const statusText = isWorking ? 'Working' : 'Idle';

            // Determine model badge class
            let modelBadgeClass = 'model-badge bg-light text-dark';
            if (agent.model.includes('gemma')) {
                modelBadgeClass = 'model-badge bg-info text-white';
            } else if (agent.model.includes('deepseek')) {
                modelBadgeClass = 'model-badge bg-success text-white';
            }

            agentCard.innerHTML = `
                <div class="agent-name">${agent.name}</div>
                <div class="agent-role">Role: ${agent.role}</div>
                <div>
                    <span class="${modelBadgeClass}">${agent.model}</span>
                    <span class="status-badge ${statusClass} text-white">${statusText}</span>
                </div>
            `;

            // Add tasks this agent is working on
            if (agentTasks.length > 0) {
                agentTasks.forEach(task => {
                    const taskDiv = document.createElement('div');
                    taskDiv.className = 'agent-task';

                    taskDiv.innerHTML = `
                        <strong>Task:</strong> ${task.title}
                        <div><strong>Status:</strong> ${task.status}</div>
                        ${task.progress > 0 ? `
                            <div class="progress mt-2" style="height: 5px;">
                                <div class="progress-bar" role="progressbar" style="width: ${task.progress}%"
                                    aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                            </div>
                        ` : ''}
                    `;

                    agentCard.appendChild(taskDiv);
                });
            }

            agentsContainer.appendChild(agentCard);
        });
    } else {
        agentsContainer.innerHTML = '<em>No agents assigned to this project yet</em>';
    }

    // Show the detail panel
    detailPanel.classList.remove('d-none');
}

// Close project details
function closeProjectDetails() {
    document.getElementById('project-detail-panel').classList.add('d-none');
}

// Render the workers status
function renderWorkers() {
    const workersContainer = document.getElementById('workers-container');
    workersContainer.innerHTML = '';

    workers.forEach(worker => {
        const workerTasks = tasks.filter(task => task.assigned_to === worker.agent_id);
        const isWorking = workerTasks.some(task => task.status === 'in_progress');
        const currentTask = workerTasks.find(task => task.status === 'in_progress');

        const workerCol = document.createElement('div');
        workerCol.className = 'col-md-6 col-lg-4 mb-3';

        const workerStatus = isWorking ? 'working' : 'idle';
        const workload = `${worker.current_workload}/${worker.max_workload}`;

        let modelBadgeClass = 'model-badge';
        if (worker.model.includes('gemma')) {
            modelBadgeClass += ' gemma';
        } else if (worker.model.includes('deepseek')) {
            modelBadgeClass += ' deepseek';
        }

        workerCol.innerHTML = `
            <div class="worker-card ${workerStatus}">
                <h3>${worker.name} <small class="text-muted">(${worker.role})</small></h3>
                <div>
                    <span class="${modelBadgeClass}">${worker.model}</span>
                    <span class="badge bg-secondary">Workload: ${workload}</span>
                </div>
                ${currentTask ? `
                    <div class="current-task">
                        <strong>Current Task:</strong> ${currentTask.title}
                        <div class="progress">
                            <div class="progress-bar" role="progressbar" style="width: ${currentTask.progress}%"
                                aria-valuenow="${currentTask.progress}" aria-valuemin="0" aria-valuemax="100"></div>
                        </div>
                    </div>
                ` : '<div class="current-task text-muted">No active task</div>'}
            </div>
        `;

        workersContainer.appendChild(workerCol);
    });
}

// Render the task flow visualization
function renderTaskFlow() {
    const priorityTasks = document.getElementById('priority-tasks');
    const designTasks = document.getElementById('design-tasks');
    const developmentTasks = document.getElementById('development-tasks');
    const testingTasks = document.getElementById('testing-tasks');
    const reviewTasks = document.getElementById('review-tasks');
    const documentationTasks = document.getElementById('documentation-tasks');

    // Clear all task lists
    priorityTasks.innerHTML = '';
    designTasks.innerHTML = '';
    developmentTasks.innerHTML = '';
    testingTasks.innerHTML = '';
    reviewTasks.innerHTML = '';
    documentationTasks.innerHTML = '';

    // Add placeholder to priority lane if empty
    const placeholder = document.createElement('div');
    placeholder.className = 'task-placeholder';
    placeholder.textContent = 'Drag tasks here for manual assignment';
    priorityTasks.appendChild(placeholder);

    // Filter tasks if a project is selected
    const filteredTasks = selectedProjectId
        ? tasks.filter(task => task.project_id === selectedProjectId)
        : tasks;

    // Sort tasks by priority (lower number = higher priority)
    const sortedTasks = [...filteredTasks].sort((a, b) => {
        // First by priority
        if (a.priority !== b.priority) {
            return a.priority - b.priority;
        }
        // Then by status (in_progress first)
        if (a.status !== b.status) {
            return a.status === 'in_progress' ? -1 : 1;
        }
        // Then by creation date (newest first)
        return new Date(b.created_at) - new Date(a.created_at);
    });

    // Group tasks by type
    sortedTasks.forEach(task => {
        const taskCard = createTaskCard(task);

        // High priority tasks (priority = 1) go to priority lane
        if (task.priority === 1) {
            // Remove placeholder if there are priority tasks
            if (priorityTasks.querySelector('.task-placeholder')) {
                priorityTasks.innerHTML = '';
            }
            priorityTasks.appendChild(taskCard);
            return;
        }

        // Other tasks go to their respective lanes
        switch (task.task_type) {
            case 'design':
                designTasks.appendChild(taskCard);
                break;
            case 'development':
                developmentTasks.appendChild(taskCard);
                break;
            case 'testing':
                testingTasks.appendChild(taskCard);
                break;
            case 'review':
                reviewTasks.appendChild(taskCard);
                break;
            case 'documentation':
                documentationTasks.appendChild(taskCard);
                break;
        }
    });
}

// Create a task card element
function createTaskCard(task) {
    const taskCard = document.createElement('div');
    taskCard.className = `task-card ${task.status} ${task.is_priority ? 'priority-task' : ''}`;
    taskCard.dataset.taskId = task.id;
    taskCard.draggable = true;

    // Find the project this task belongs to
    const project = projects.find(p => p.id === task.project_id);
    const projectName = project ? project.title : 'Unknown Project';

    // Find the worker assigned to this task
    const worker = workers.find(w => w.agent_id === task.assigned_to);
    const assignedTo = worker ? worker.name : 'Unassigned';

    // Determine if download button should be shown
    const showDownloadButton = task.status === 'completed' || task.has_result;

    // Create agent selection dropdown
    const agentOptions = workers
        .filter(w => w.agent_type === 'worker')
        .map(w => `<option value="${w.agent_id}" ${task.assigned_to === w.agent_id ? 'selected' : ''}>${w.name} (${w.role})</option>`)
        .join('');

    taskCard.innerHTML = `
        <div class="d-flex justify-content-between align-items-start">
            <div class="task-title">${task.title}</div>
            <button class="btn btn-sm btn-outline-danger delete-task-btn" data-task-id="${task.id}">
                <i class="bi bi-trash"></i>
            </button>
        </div>
        <div class="task-project">Project: ${projectName}</div>
        <div class="task-assigned">
            <div class="d-flex align-items-center">
                <label class="me-2">Assign to:</label>
                <select class="form-select form-select-sm agent-select" data-task-id="${task.id}">
                    <option value="">Unassigned</option>
                    ${agentOptions}
                </select>
                <button class="btn btn-sm btn-primary ms-2 prioritize-btn" data-task-id="${task.id}">
                    Prioritize
                </button>
            </div>
        </div>
        ${task.progress > 0 ? `
            <div class="progress mt-2" style="height: 5px;">
                <div class="progress-bar" role="progressbar" style="width: ${task.progress}%"
                    aria-valuenow="${task.progress}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>
        ` : ''}
        ${showDownloadButton ? `
            <div class="task-actions mt-2">
                <button class="btn btn-sm btn-outline-primary download-result-btn" data-task-id="${task.id}">
                    <i class="bi bi-download"></i> Download Result
                </button>
            </div>
        ` : ''}
    `;

    // Add event listener for download button
    if (showDownloadButton) {
        setTimeout(() => {
            const downloadBtn = taskCard.querySelector('.download-result-btn');
            if (downloadBtn) {
                downloadBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    downloadTaskResult(task.id);
                });
            }
        }, 0);
    }

    // Add event listener for agent selection
    setTimeout(() => {
        const agentSelect = taskCard.querySelector('.agent-select');
        if (agentSelect) {
            agentSelect.addEventListener('change', (e) => {
                e.stopPropagation();
                assignTaskToAgent(task.id, e.target.value);
            });
        }

        // Add event listener for prioritize button
        const prioritizeBtn = taskCard.querySelector('.prioritize-btn');
        if (prioritizeBtn) {
            prioritizeBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                prioritizeTask(task.id);
            });
        }

        // Add event listener for delete button
        const deleteBtn = taskCard.querySelector('.delete-task-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                if (confirm(`Are you sure you want to delete task "${task.title}"?`)) {
                    deleteTask(task.id);
                }
            });
        }
    }, 0);

    return taskCard;
}

// Download task result
async function downloadTaskResult(taskId) {
    try {
        console.log(`Downloading result for task ${taskId}...`);

        // Fetch task result
        const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/result`);
        if (!response.ok) {
            throw new Error(`Failed to fetch task result: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        console.log('Task result:', result);

        // Create a formatted text with task details and result
        let formattedText = `# ${result.title}\n\n`;
        formattedText += `Status: ${result.status}\n`;
        formattedText += `Created: ${result.created_at}\n`;
        formattedText += `Updated: ${result.updated_at}\n`;
        formattedText += `Completed: ${result.completed_at || 'Not completed'}\n`;
        formattedText += `Progress: ${result.progress}%\n\n`;

        formattedText += `## Task Result\n\n${result.result || 'No result available'}\n\n`;

        formattedText += `## Task Updates\n\n`;
        if (result.updates && result.updates.length > 0) {
            result.updates.forEach(update => {
                formattedText += `### ${new Date(update.timestamp).toLocaleString()}\n`;
                formattedText += `${update.content}\n\n`;
            });
        } else {
            formattedText += 'No updates available\n';
        }

        // Create a blob and download
        const blob = new Blob([formattedText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `task-${taskId}-result.md`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showSuccess(`Downloaded result for task ${taskId}`);
    } catch (error) {
        console.error('Error downloading task result:', error);
        showError(`Failed to download task result: ${error.message}`);
    }
}

// Helper function to get badge class based on status
function getStatusBadgeClass(status) {
    switch (status) {
        case 'pending':
            return 'bg-secondary';
        case 'in_progress':
            return 'bg-primary';
        case 'completed':
            return 'bg-success';
        case 'failed':
            return 'bg-danger';
        default:
            return 'bg-secondary';
    }
}

// Show success message
function showSuccess(message) {
    console.log('Success:', message);

    // Create a Bootstrap alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to the top of the page
    document.querySelector('.container-fluid').prepend(alertDiv);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 5000);
}

// Show error message
function showError(message) {
    console.error('Error:', message);

    // Create a Bootstrap alert
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.setAttribute('role', 'alert');

    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to the top of the page
    document.querySelector('.container-fluid').prepend(alertDiv);

    // Auto-dismiss after 10 seconds
    setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alertDiv);
        bsAlert.close();
    }, 10000);
}

// Agent Management Functions
let availableEndpoints = [
    'localhost:11434',
    'ruocco.uk:11434',
    '192.168.0.39:11434'
];

let availableModels = [
    'gemma3:1b',
    'gemma3:4b',
    'deepseek-coder:16b'
];

// Open the agent management modal
function openAgentManagementModal() {
    populateAgentConfigTable();
    const modal = new bootstrap.Modal(document.getElementById('agentManagementModal'));
    modal.show();
}

// Set up agent management
function setupAgentManagement() {
    // Add endpoint button
    document.getElementById('add-endpoint-btn').addEventListener('click', addCustomEndpoint);

    // Save agent config button
    document.getElementById('save-agent-config-btn').addEventListener('click', saveAllAgentConfigs);
}

// Add a custom endpoint
function addCustomEndpoint() {
    const customEndpointInput = document.getElementById('custom-endpoint');
    const customEndpoint = customEndpointInput.value.trim();

    if (customEndpoint && !availableEndpoints.includes(customEndpoint)) {
        availableEndpoints.push(customEndpoint);

        // Add checkbox for the new endpoint
        const endpointsContainer = document.querySelector('.mb-3 .row.mb-2');
        const col = document.createElement('div');
        col.className = 'col';
        col.innerHTML = `
            <div class="form-check">
                <input class="form-check-input" type="checkbox" id="endpoint-custom-${availableEndpoints.length}" checked>
                <label class="form-check-label" for="endpoint-custom-${availableEndpoints.length}">
                    ${customEndpoint}
                </label>
            </div>
        `;
        endpointsContainer.appendChild(col);

        // Clear the input
        customEndpointInput.value = '';

        // Refresh the agent config table
        populateAgentConfigTable();
    }
}

// Populate the agent configuration table
function populateAgentConfigTable() {
    const tableBody = document.getElementById('agent-config-table');
    tableBody.innerHTML = '';

    workers.forEach(agent => {
        const tr = document.createElement('tr');

        // Create model select dropdown
        const modelSelect = document.createElement('select');
        modelSelect.className = 'model-select';
        modelSelect.dataset.agentId = agent.agent_id;

        availableModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            option.selected = agent.model === model;
            modelSelect.appendChild(option);
        });

        // Create endpoint select dropdown
        const endpointSelect = document.createElement('select');
        endpointSelect.className = 'endpoint-select';
        endpointSelect.dataset.agentId = agent.agent_id;

        availableEndpoints.forEach(endpoint => {
            const option = document.createElement('option');
            option.value = endpoint;
            option.textContent = endpoint;

            // Try to determine the current endpoint from the agent's configuration
            let currentEndpoint = 'localhost:11434'; // Default
            if (agent.model.includes('gemma3:4b')) {
                currentEndpoint = 'ruocco.uk:11434';
            } else if (agent.model.includes('gemma3:1b')) {
                currentEndpoint = '192.168.0.39:11434';
            }

            option.selected = endpoint === currentEndpoint;
            endpointSelect.appendChild(option);
        });

        // Create action buttons
        const saveBtn = document.createElement('button');
        saveBtn.className = 'btn btn-sm btn-primary save-agent-btn';
        saveBtn.textContent = 'Save';
        saveBtn.dataset.agentId = agent.agent_id;
        saveBtn.addEventListener('click', () => saveAgentConfig(agent.agent_id));

        const resetBtn = document.createElement('button');
        resetBtn.className = 'btn btn-sm btn-secondary reset-agent-btn';
        resetBtn.textContent = 'Reset';
        resetBtn.dataset.agentId = agent.agent_id;
        resetBtn.addEventListener('click', () => resetAgentConfig(agent.agent_id));

        // Add all elements to the row
        tr.innerHTML = `
            <td>${agent.name}</td>
            <td>${agent.role}</td>
            <td id="model-cell-${agent.agent_id}"></td>
            <td id="endpoint-cell-${agent.agent_id}"></td>
            <td id="actions-cell-${agent.agent_id}"></td>
        `;

        tableBody.appendChild(tr);

        // Add the elements to their cells
        document.getElementById(`model-cell-${agent.agent_id}`).appendChild(modelSelect);
        document.getElementById(`endpoint-cell-${agent.agent_id}`).appendChild(endpointSelect);

        const actionsCell = document.getElementById(`actions-cell-${agent.agent_id}`);
        actionsCell.appendChild(saveBtn);
        actionsCell.appendChild(resetBtn);
    });
}

// Save agent configuration
async function saveAgentConfig(agentId) {
    const modelSelect = document.querySelector(`.model-select[data-agent-id="${agentId}"]`);
    const endpointSelect = document.querySelector(`.endpoint-select[data-agent-id="${agentId}"]`);

    const model = modelSelect.value;
    const endpoint = endpointSelect.value;

    try {
        const response = await fetch(`/api/agents/${agentId}/config`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model,
                endpoint
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to update agent configuration: ${response.status} ${response.statusText}`);
        }

        const updatedAgent = await response.json();

        // Update the agent in the workers array
        const agentIndex = workers.findIndex(a => a.agent_id === agentId);
        if (agentIndex !== -1) {
            workers[agentIndex] = updatedAgent;
        }

        showSuccess(`Agent ${updatedAgent.name} configuration updated successfully!`);
    } catch (error) {
        console.error('Error updating agent configuration:', error);
        showError(`Failed to update agent configuration: ${error.message}`);
    }
}

// Reset agent configuration
function resetAgentConfig(agentId) {
    const agent = workers.find(a => a.agent_id === agentId);
    if (!agent) return;

    const modelSelect = document.querySelector(`.model-select[data-agent-id="${agentId}"]`);
    const endpointSelect = document.querySelector(`.endpoint-select[data-agent-id="${agentId}"]`);

    // Reset to current values
    modelSelect.value = agent.model;

    // Try to determine the current endpoint from the agent's configuration
    let currentEndpoint = 'localhost:11434'; // Default
    if (agent.model.includes('gemma3:4b')) {
        currentEndpoint = 'ruocco.uk:11434';
    } else if (agent.model.includes('gemma3:1b')) {
        currentEndpoint = '192.168.0.39:11434';
    }

    endpointSelect.value = currentEndpoint;
}

// Save all agent configurations
async function saveAllAgentConfigs() {
    const saveButtons = document.querySelectorAll('.save-agent-btn');

    // Create a promise for each save operation
    const savePromises = Array.from(saveButtons).map(button => {
        const agentId = button.dataset.agentId;
        return saveAgentConfig(agentId);
    });

    try {
        await Promise.all(savePromises);
        showSuccess('All agent configurations saved successfully!');

        // Close the modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('agentManagementModal'));
        modal.hide();

        // Refresh the workers display
        fetchWorkers().then(renderWorkers);
    } catch (error) {
        console.error('Error saving all agent configurations:', error);
        showError(`Failed to save all agent configurations: ${error.message}`);
    }
}

// Assign a task to a specific agent
async function assignTaskToAgent(taskId, agentId) {
    try {
        console.log(`Assigning task ${taskId} to agent ${agentId}`);

        // Make API call to assign task
        const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/assign`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                agent_id: agentId
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to assign task: ${response.status} ${response.statusText}`);
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
        const agentName = agentId ? workers.find(w => w.agent_id === agentId)?.name || 'Unknown agent' : 'Unassigned';
        showSuccess(`Task "${updatedTask.title}" assigned to ${agentName}`);
    } catch (error) {
        console.error('Error assigning task:', error);
        showError(`Failed to assign task: ${error.message}`);
    }
}

// Prioritize a task
async function prioritizeTask(taskId) {
    try {
        console.log(`Prioritizing task ${taskId}`);

        // Make API call to prioritize task
        const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/prioritize`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to prioritize task: ${response.status} ${response.statusText}`);
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
        showSuccess(`Task "${updatedTask.title}" prioritized successfully`);
    } catch (error) {
        console.error('Error prioritizing task:', error);
        showError(`Failed to prioritize task: ${error.message}`);
    }
}

// Delete a task
async function deleteTask(taskId) {
    try {
        console.log(`Deleting task ${taskId}`);

        // Make API call to delete task
        const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to delete task: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        // Remove task from local data
        tasks = tasks.filter(t => t.id !== taskId);

        // Refresh UI
        renderUI();

        // Show success message
        showSuccess(result.message);
    } catch (error) {
        console.error('Error deleting task:', error);
        showError(`Failed to delete task: ${error.message}`);
    }
}

// Delete all tasks for a project
async function deleteAllProjectTasks(projectId) {
    try {
        console.log(`Deleting all tasks for project ${projectId}`);

        // Make API call to delete all project tasks
        const response = await fetch(`${API_BASE_URL}/api/projects/${projectId}/tasks`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to delete project tasks: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();

        // Remove tasks from local data
        tasks = tasks.filter(t => t.project_id !== projectId);

        // Refresh UI
        renderUI();

        // Show success message
        showSuccess(result.message);
    } catch (error) {
        console.error('Error deleting project tasks:', error);
        showError(`Failed to delete project tasks: ${error.message}`);
    }
}
