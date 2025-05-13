// API base URL
const API_BASE_URL = '/api/v1';

// DOM elements
const dashboardView = document.getElementById('dashboard-view');
const tasksView = document.getElementById('tasks-view');
const agentsView = document.getElementById('agents-view');
const discussionsView = document.getElementById('discussions-view');

// Advanced task form elements
const allowCollaboration = document.getElementById('allow-collaboration');
const collaborationSettings = document.querySelector('.collaboration-settings');

// Agent modal elements
const createAgentModal = new bootstrap.Modal(document.getElementById('createAgentModal'));
const editAgentModal = new bootstrap.Modal(document.getElementById('editAgentModal'));
const createAgentBtn = document.getElementById('create-agent-btn');
const updateAgentBtn = document.getElementById('update-agent-btn');

const dashboardLink = document.getElementById('dashboard-link');
const tasksLink = document.getElementById('tasks-link');
const agentsLink = document.getElementById('agents-link');
const discussionsLink = document.getElementById('discussions-link');

const recentTasksContainer = document.getElementById('recent-tasks-container');
const allAgentsContainer = document.getElementById('all-agents-container');
const agentStatusContainer = document.getElementById('agent-status-container');
const tasksContainer = document.getElementById('tasks-container');
const agentsContainer = document.getElementById('agents-container');
const discussionsContainer = document.getElementById('discussions-container');

const activeAgentsCount = document.getElementById('active-agents-count');
const pendingTasksCount = document.getElementById('pending-tasks-count');
const completedTasksCount = document.getElementById('completed-tasks-count');

const refreshDashboardBtn = document.getElementById('refresh-dashboard');
const createTaskBtn = document.getElementById('create-task-btn');
const createDiscussionBtn = document.getElementById('create-discussion-btn');

const taskComplexitySlider = document.getElementById('task-complexity');
const taskPrioritySlider = document.getElementById('task-priority');
const complexityValue = document.getElementById('complexity-value');
const priorityValue = document.getElementById('priority-value');

// Navigation
dashboardLink.addEventListener('click', (e) => {
    e.preventDefault();
    showView(dashboardView);
    dashboardLink.classList.add('active');
    tasksLink.classList.remove('active');
    agentsLink.classList.remove('active');
    discussionsLink.classList.remove('active');
    loadDashboardData();
});

tasksLink.addEventListener('click', (e) => {
    e.preventDefault();
    showView(tasksView);
    dashboardLink.classList.remove('active');
    tasksLink.classList.add('active');
    agentsLink.classList.remove('active');
    discussionsLink.classList.remove('active');
    loadTasks();
});

agentsLink.addEventListener('click', (e) => {
    e.preventDefault();
    showView(agentsView);
    dashboardLink.classList.remove('active');
    tasksLink.classList.remove('active');
    agentsLink.classList.add('active');
    discussionsLink.classList.remove('active');
    loadAgents();
});

discussionsLink.addEventListener('click', (e) => {
    e.preventDefault();
    showView(discussionsView);
    dashboardLink.classList.remove('active');
    tasksLink.classList.remove('active');
    agentsLink.classList.remove('active');
    discussionsLink.classList.add('active');
    loadDiscussions();
});

// Show view
function showView(view) {
    dashboardView.style.display = 'none';
    tasksView.style.display = 'none';
    agentsView.style.display = 'none';
    discussionsView.style.display = 'none';
    view.style.display = 'block';
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load recent tasks
        const tasksResponse = await fetch(`${API_BASE_URL}/tasks?limit=5`);
        const tasksData = await tasksResponse.json();

        // Load agent status
        const agentsResponse = await fetch(`${API_BASE_URL}/agents`);
        const agentsData = await agentsResponse.json();

        // Update counts
        const availableAgents = agentsData.agents.filter(agent => agent.status === 'available').length;
        const busyAgents = agentsData.agents.filter(agent => agent.status === 'busy').length;
        activeAgentsCount.textContent = availableAgents + busyAgents;

        const pendingTasks = await fetch(`${API_BASE_URL}/tasks?status=not_started&limit=1`);
        const pendingTasksData = await pendingTasks.json();
        pendingTasksCount.textContent = pendingTasksData.total;

        const completedTasks = await fetch(`${API_BASE_URL}/tasks?status=complete&limit=1`);
        const completedTasksData = await completedTasks.json();
        completedTasksCount.textContent = completedTasksData.total;

        // Render all agents
        renderAllAgents(agentsData.agents);

        // Render recent tasks
        renderRecentTasks(tasksData.tasks);
    } catch (error) {
        console.error('Error loading dashboard data:', error);
        showError('Failed to load dashboard data. Please try again.');
    }
}

// Render recent tasks
function renderRecentTasks(tasks) {
    if (tasks.length === 0) {
        recentTasksContainer.innerHTML = '<div class="text-center py-3">No tasks found</div>';
        return;
    }

    let html = '';
    tasks.forEach(task => {
        const statusClass = getStatusClass(task.status);
        const complexityClass = getComplexityClass(task.complexity);

        html += `
            <div class="card task-card ${statusClass} mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="card-title mb-0">${task.title}</h5>
                        <span class="badge badge-complexity ${complexityClass}">Complexity: ${task.complexity}</span>
                    </div>
                    <p class="card-text text-muted small">${truncateText(task.description, 100)}</p>
                    <div class="progress mb-2">
                        <div class="progress-bar" role="progressbar" style="width: ${task.stage_progress}%"></div>
                    </div>
                    <div class="mb-2">
                        <div class="workflow-badges small">
                            <span class="badge ${task.status === 'not_started' ? 'bg-primary' : 'bg-secondary text-white-50'}">NS</span>
                            <span class="badge ${task.status === 'design' ? 'bg-primary' : 'bg-secondary text-white-50'}">D</span>
                            <span class="badge ${task.status === 'build' ? 'bg-primary' : 'bg-secondary text-white-50'}">B</span>
                            <span class="badge ${task.status === 'test' ? 'bg-primary' : 'bg-secondary text-white-50'}">T</span>
                            <span class="badge ${task.status === 'review' ? 'bg-primary' : 'bg-secondary text-white-50'}">R</span>
                            <span class="badge ${task.status === 'complete' ? 'bg-success' : 'bg-secondary text-white-50'}">C</span>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            ${task.status !== 'not_started' && task.assigned_agent_name ?
                                `<span class="badge bg-primary ms-1 working-badge">
                                    <i class="bi bi-person-workspace"></i> ${task.assigned_agent_name}
                                </span>` : ''
                            }
                        </div>
                        <small class="text-muted">${formatDate(task.created_at)}</small>
                    </div>
                </div>
            </div>
        `;
    });

    recentTasksContainer.innerHTML = html;
}

// Render all agents
function renderAllAgents(agents) {
    if (agents.length === 0) {
        allAgentsContainer.innerHTML = '<div class="text-center py-3">No agents found</div>';
        return;
    }

    let html = '';
    agents.forEach(agent => {
        const statusClass = getAgentStatusClass(agent.status);

        html += `
            <div class="col-md-4 mb-4">
                <div class="card agent-card h-100">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5 class="mb-0">${agent.name}</h5>
                        <div>
                            <span class="status-indicator status-${agent.status}"></span>
                            <span class="badge bg-secondary">${formatAgentStatus(agent.status)}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="card-text"><strong>Model:</strong> ${agent.model}</p>
                        <p class="card-text"><strong>Complexity:</strong> ${agent.min_complexity}-${agent.max_complexity}</p>

                        ${agent.status === 'busy' && agent.current_task ? `
                        <div class="alert alert-info mt-3 mb-3">
                            <strong>Working on:</strong> ${agent.current_task.title}
                            <div class="mb-2">
                                <span class="badge ${agent.current_task.status === 'design' ? 'bg-primary' : 'bg-secondary text-white-50'}">Design</span>
                                <span class="badge ${agent.current_task.status === 'build' ? 'bg-primary' : 'bg-secondary text-white-50'}">Build</span>
                                <span class="badge ${agent.current_task.status === 'test' ? 'bg-primary' : 'bg-secondary text-white-50'}">Test</span>
                                <span class="badge ${agent.current_task.status === 'review' ? 'bg-primary' : 'bg-secondary text-white-50'}">Review</span>
                            </div>
                            <div class="progress mt-2" style="height: 8px;">
                                <div class="progress-bar bg-info" role="progressbar" style="width: ${agent.current_task.stage_progress}%"></div>
                            </div>
                            <div class="d-flex justify-content-between mt-2">
                                <span class="badge bg-secondary">${formatStatus(agent.current_task.status)}</span>
                                <small class="text-muted">Updated: ${formatDate(agent.current_task.updated_at)}</small>
                            </div>
                        </div>
                        ` : `
                        <div class="alert alert-light mt-3 mb-3">
                            <p class="mb-0 text-center">
                                ${agent.status === 'available' ? 'Available for new tasks' : 'Offline'}
                            </p>
                        </div>
                        `}
                    </div>
                    <div class="card-footer d-flex justify-content-between align-items-center">
                        <small class="text-muted">Last active: ${formatDate(agent.last_active)}</small>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" onclick="viewAgentDetails('${agent.id}')">
                                <i class="bi bi-eye"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-secondary ms-1" onclick="toggleAgentStatus('${agent.id}', '${agent.status}')">
                                ${agent.status === 'offline' ? '<i class="bi bi-play"></i>' : '<i class="bi bi-pause"></i>'}
                            </button>
                            <button class="btn btn-sm btn-outline-warning ms-1" onclick="editAgent('${agent.id}')">
                                <i class="bi bi-pencil"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    allAgentsContainer.innerHTML = html;
}

// Load tasks
async function loadTasks() {
    try {
        const response = await fetch(`${API_BASE_URL}/tasks`);
        const data = await response.json();
        renderTasks(data.tasks);
    } catch (error) {
        console.error('Error loading tasks:', error);
        showError('Failed to load tasks. Please try again.');
    }
}

// Render tasks
function renderTasks(tasks) {
    if (tasks.length === 0) {
        tasksContainer.innerHTML = '<div class="text-center py-3">No tasks found</div>';
        return;
    }

    let html = '';
    tasks.forEach(task => {
        const statusClass = getStatusClass(task.status);
        const complexityClass = getComplexityClass(task.complexity);

        html += `
            <div class="card task-card ${statusClass} mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="card-title mb-0">${task.title}</h5>
                        <div>
                            <span class="badge badge-complexity ${complexityClass}">Complexity: ${task.complexity}</span>
                            <span class="badge bg-secondary ms-1">Priority: ${task.priority}</span>
                        </div>
                    </div>
                    <p class="card-text">${task.description}</p>
                    <div class="progress mb-2">
                        <div class="progress-bar" role="progressbar" style="width: ${task.stage_progress}%"></div>
                    </div>

                    ${task.research_likelihood ?
                        `<div class="mb-2"><small class="text-muted">Research: <span class="badge bg-info">${task.research_likelihood}</span></small></div>` : ''}

                    ${task.output_formats && task.output_formats.length > 0 ?
                        `<div class="mb-2"><small class="text-muted">Formats: ${task.output_formats.map(f => `<span class="badge bg-light text-dark">${f}</span>`).join(' ')}</small></div>` : ''}

                    ${task.deadline ?
                        `<div class="mb-2"><small class="text-muted">Deadline: ${formatDate(task.deadline)}</small></div>` : ''}

                    <div class="mb-2">
                        <div class="workflow-badges">
                            <span class="badge ${task.status === 'not_started' ? 'bg-primary' : 'bg-secondary text-white-50'}">Not Started</span>
                            <span class="badge ${task.status === 'design' ? 'bg-primary' : 'bg-secondary text-white-50'}">Design</span>
                            <span class="badge ${task.status === 'build' ? 'bg-primary' : 'bg-secondary text-white-50'}">Build</span>
                            <span class="badge ${task.status === 'test' ? 'bg-primary' : 'bg-secondary text-white-50'}">Test</span>
                            <span class="badge ${task.status === 'review' ? 'bg-primary' : 'bg-secondary text-white-50'}">Review</span>
                            <span class="badge ${task.status === 'complete' ? 'bg-success' : 'bg-secondary text-white-50'}">Complete</span>
                        </div>
                    </div>
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            ${task.status !== 'not_started' && task.assigned_agent_name ?
                                `<span class="badge bg-primary ms-1 working-badge">
                                    <i class="bi bi-person-workspace"></i> ${task.assigned_agent_name}
                                </span>` :
                                (task.assigned_agent_id ? `<span class="badge bg-info ms-1">Assigned</span>` : '')
                            }
                            ${task.allow_collaboration ? `<span class="badge bg-success ms-1">Collaborative</span>` : ''}
                        </div>
                        <div>
                            <small class="text-muted">Created: ${formatDate(task.created_at)}</small>
                            <button class="btn btn-sm btn-outline-primary ms-2" onclick="viewTaskDetails('${task.id}')">
                                <i class="bi bi-eye"></i> View
                            </button>
                            ${task.status === 'complete' && task.result_path ?
                                `<button class="btn btn-sm btn-outline-success ms-1" onclick="downloadTaskOutput('${task.id}')">
                                    <i class="bi bi-download"></i> Download
                                </button>` : ''
                            }
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    tasksContainer.innerHTML = html;
}

// Load agents
async function loadAgents() {
    try {
        const response = await fetch(`${API_BASE_URL}/agents`);
        const data = await response.json();
        renderAgents(data.agents);
    } catch (error) {
        console.error('Error loading agents:', error);
        showError('Failed to load agents. Please try again.');
    }
}

// Render agents
function renderAgents(agents) {
    if (agents.length === 0) {
        agentsContainer.innerHTML = '<div class="text-center py-3">No agents found</div>';
        return;
    }

    let html = '';
    agents.forEach(agent => {
        const statusClass = getAgentStatusClass(agent.status);

        html += `
            <div class="card agent-card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="card-title mb-0">${agent.name}</h5>
                        <div>
                            <span class="status-indicator status-${agent.status}"></span>
                            <span class="badge bg-secondary">${formatAgentStatus(agent.status)}</span>
                        </div>
                    </div>
                    <p class="card-text">Model: ${agent.model}</p>
                    <p class="card-text">Endpoint: ${agent.endpoint}</p>
                    <p class="card-text">Complexity Range: ${agent.min_complexity}-${agent.max_complexity}</p>

                    ${agent.status === 'busy' && agent.current_task ? `
                    <div class="alert alert-info mt-3 mb-3">
                        <strong>Working on:</strong> ${agent.current_task.title}
                        <div class="progress mt-2" style="height: 8px;">
                            <div class="progress-bar bg-info" role="progressbar" style="width: ${agent.current_task.stage_progress}%"></div>
                        </div>
                        <div class="d-flex justify-content-between mt-2">
                            <span class="badge bg-secondary">${formatStatus(agent.current_task.status)}</span>
                            <small class="text-muted">Updated: ${formatDate(agent.current_task.updated_at)}</small>
                        </div>
                    </div>
                    ` : ''}

                    <div class="d-flex justify-content-between align-items-center">
                        <small class="text-muted">Created: ${formatDate(agent.created_at)}</small>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" onclick="viewAgentDetails('${agent.id}')">
                                <i class="bi bi-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-secondary ms-1" onclick="toggleAgentStatus('${agent.id}', '${agent.status}')">
                                ${agent.status === 'offline' ? '<i class="bi bi-play"></i> Activate' : '<i class="bi bi-pause"></i> Pause'}
                            </button>
                            <button class="btn btn-sm btn-outline-warning ms-1" onclick="editAgent('${agent.id}')">
                                <i class="bi bi-pencil"></i> Edit
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    agentsContainer.innerHTML = html;
}

// Load discussions
async function loadDiscussions() {
    try {
        const response = await fetch(`${API_BASE_URL}/discussions`);
        const data = await response.json();
        renderDiscussions(data.sessions);
    } catch (error) {
        console.error('Error loading discussions:', error);
        showError('Failed to load discussions. Please try again.');
    }
}

// Render discussions
function renderDiscussions(discussions) {
    if (discussions.length === 0) {
        discussionsContainer.innerHTML = '<div class="text-center py-3">No discussions found</div>';
        return;
    }

    let html = '';
    discussions.forEach(discussion => {
        const statusClass = discussion.status === 'active' ? 'bg-success' : 'bg-secondary';

        html += `
            <div class="card mb-3">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <h5 class="card-title mb-0">${discussion.title}</h5>
                        <span class="badge ${statusClass}">${discussion.status}</span>
                    </div>
                    ${discussion.system_prompt ? `<p class="card-text text-muted small">${truncateText(discussion.system_prompt, 100)}</p>` : ''}
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            ${renderTags(discussion.tags)}
                        </div>
                        <div>
                            <small class="text-muted">Created: ${formatDate(discussion.created_at)}</small>
                            <button class="btn btn-sm btn-outline-primary ms-2" onclick="openDiscussion('${discussion.id}')">
                                <i class="bi bi-chat"></i> Open
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    });

    discussionsContainer.innerHTML = html;
}

// Helper functions
function getStatusClass(status) {
    switch (status) {
        case 'design': return 'design';
        case 'build': return 'build';
        case 'test': return 'test';
        case 'review': return 'review';
        case 'complete': return 'complete';
        default: return '';
    }
}

function getComplexityClass(complexity) {
    if (complexity <= 3) return 'low';
    if (complexity <= 7) return 'medium';
    return 'high';
}

function getAgentStatusClass(status) {
    switch (status) {
        case 'available': return 'available';
        case 'busy': return 'busy';
        case 'offline': return 'offline';
        default: return '';
    }
}

function formatStatus(status) {
    return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ');
}

function formatAgentStatus(status) {
    return status.charAt(0).toUpperCase() + status.slice(1);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString();
}

function truncateText(text, maxLength) {
    if (!text) return '';
    return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
}

function renderTags(tags) {
    if (!tags || tags.length === 0) return '';

    let html = '';
    tags.forEach(tag => {
        html += `<span class="badge bg-light text-dark me-1">${tag}</span>`;
    });

    return html;
}

function showError(message) {
    // Implement error notification
    console.error(message);
    alert(message);
}

// Event listeners
refreshDashboardBtn.addEventListener('click', loadDashboardData);

taskComplexitySlider.addEventListener('input', () => {
    complexityValue.textContent = taskComplexitySlider.value;
});

taskPrioritySlider.addEventListener('input', () => {
    priorityValue.textContent = taskPrioritySlider.value;
});

// Show/hide collaboration settings based on checkbox
allowCollaboration.addEventListener('change', () => {
    if (allowCollaboration.checked) {
        collaborationSettings.style.display = 'block';
    } else {
        collaborationSettings.style.display = 'none';
    }
});

createTaskBtn.addEventListener('click', async () => {
    const title = document.getElementById('task-title').value;
    const description = document.getElementById('task-description').value;
    const complexity = parseInt(taskComplexitySlider.value);
    const priority = parseInt(taskPrioritySlider.value);

    // Get advanced options
    const researchLikelihood = document.getElementById('task-research-likelihood').value;

    // Get output formats
    const outputFormats = [];
    document.querySelectorAll('input[id^="format-"]:checked').forEach(checkbox => {
        outputFormats.push(checkbox.value);
    });

    // Get allowed tools
    const allowedTools = [];
    document.querySelectorAll('input[id^="tool-"]:checked').forEach(checkbox => {
        allowedTools.push(checkbox.value);
    });

    // Get collaboration settings
    const allowCollaborationChecked = document.getElementById('allow-collaboration').checked;
    const maxCollaborators = allowCollaborationChecked ?
        parseInt(document.getElementById('max-collaborators').value) : null;

    // Get human review setting
    const humanReviewRequired = document.getElementById('human-review-required').checked;

    // Get deadline
    const deadlineInput = document.getElementById('task-deadline').value;
    const deadline = deadlineInput ? new Date(deadlineInput).toISOString() : null;

    if (!title || !description) {
        showError('Please fill in all required fields');
        return;
    }

    try {
        const taskData = {
            title,
            description,
            complexity,
            priority
        };

        // Add advanced options if provided
        if (researchLikelihood) {
            taskData.research_likelihood = researchLikelihood;
        }

        if (outputFormats.length > 0) {
            taskData.output_formats = outputFormats;
        }

        if (allowedTools.length > 0) {
            taskData.allowed_tools = allowedTools;
        }

        taskData.allow_collaboration = allowCollaborationChecked;

        if (maxCollaborators) {
            taskData.max_collaborators = maxCollaborators;
        }

        taskData.human_review_required = humanReviewRequired;

        if (deadline) {
            taskData.deadline = deadline;
        }

        console.log('Task data being sent:', taskData);

        // Convert enum values to strings
        if (taskData.research_likelihood) {
            taskData.research_likelihood = taskData.research_likelihood.toString();
        }

        if (taskData.output_formats && Array.isArray(taskData.output_formats)) {
            taskData.output_formats = taskData.output_formats.map(format => format.toString());
        }

        console.log('Task data after conversion:', taskData);

        const response = await fetch(`${API_BASE_URL}/tasks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(taskData)
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Server error response:', errorText);
            throw new Error(`Failed to create task: ${response.status} - ${errorText}`);
        }

        const task = await response.json();

        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('createTaskModal'));
        modal.hide();

        // Reset form
        document.getElementById('create-task-form').reset();
        complexityValue.textContent = '5';
        priorityValue.textContent = '5';
        collaborationSettings.style.display = 'none';

        // Reload data
        if (dashboardView.style.display !== 'none') {
            loadDashboardData();
        } else if (tasksView.style.display !== 'none') {
            loadTasks();
        }

        // Show success message
        alert('Task created successfully');
    } catch (error) {
        console.error('Error creating task:', error);
        showError('Failed to create task. Please try again.');
    }
});

// Toggle agent status
async function toggleAgentStatus(agentId, currentStatus) {
    const newStatus = currentStatus === 'offline' ? 'available' : 'offline';

    try {
        const response = await fetch(`${API_BASE_URL}/agents/${agentId}/status`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ status: newStatus })
        });

        if (!response.ok) {
            throw new Error(`Failed to update agent status: ${response.status}`);
        }

        // Reload agents
        if (dashboardView.style.display !== 'none') {
            loadDashboardData();
        } else if (agentsView.style.display !== 'none') {
            loadAgents();
        }

        // Show success message
        alert(`Agent ${newStatus === 'available' ? 'activated' : 'paused'} successfully`);
    } catch (error) {
        console.error('Error updating agent status:', error);
        showError('Failed to update agent status. Please try again.');
    }
}

// Edit agent
async function editAgent(agentId) {
    try {
        const response = await fetch(`${API_BASE_URL}/agents/${agentId}`);

        if (!response.ok) {
            throw new Error(`Failed to fetch agent: ${response.status}`);
        }

        const agent = await response.json();

        // Populate form fields
        document.getElementById('edit-agent-id').value = agent.id;
        document.getElementById('edit-agent-name').value = agent.name;
        document.getElementById('edit-agent-model').value = agent.model;
        document.getElementById('edit-agent-endpoint').value = agent.endpoint;
        document.getElementById('edit-agent-min-complexity').value = agent.min_complexity;
        document.getElementById('edit-agent-max-complexity').value = agent.max_complexity;

        // Show modal
        editAgentModal.show();
    } catch (error) {
        console.error('Error fetching agent:', error);
        showError('Failed to fetch agent details. Please try again.');
    }
}

// Update agent
updateAgentBtn.addEventListener('click', async () => {
    const agentId = document.getElementById('edit-agent-id').value;
    const name = document.getElementById('edit-agent-name').value;
    const model = document.getElementById('edit-agent-model').value;
    const endpoint = document.getElementById('edit-agent-endpoint').value;
    const minComplexity = parseInt(document.getElementById('edit-agent-min-complexity').value);
    const maxComplexity = parseInt(document.getElementById('edit-agent-max-complexity').value);

    if (!name || !model || !endpoint || isNaN(minComplexity) || isNaN(maxComplexity)) {
        showError('Please fill in all required fields');
        return;
    }

    if (minComplexity > maxComplexity) {
        showError('Minimum complexity cannot be greater than maximum complexity');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/agents/${agentId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                model,
                endpoint,
                min_complexity: minComplexity,
                max_complexity: maxComplexity
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to update agent: ${response.status}`);
        }

        // Close modal
        editAgentModal.hide();

        // Reset form
        document.getElementById('edit-agent-form').reset();

        // Reload agents
        if (dashboardView.style.display !== 'none') {
            loadDashboardData();
        } else if (agentsView.style.display !== 'none') {
            loadAgents();
        }

        // Show success message
        alert('Agent updated successfully');
    } catch (error) {
        console.error('Error updating agent:', error);
        showError('Failed to update agent. Please try again.');
    }
});

// Download task output
async function downloadTaskOutput(taskId, format = 'zip') {
    try {
        // Open the download URL in a new tab
        window.open(`${API_BASE_URL}/tasks/${taskId}/download?format=${format}`, '_blank');
    } catch (error) {
        console.error('Error downloading task output:', error);
        showError('Failed to download task output. Please try again.');
    }
}

// Create agent
createAgentBtn.addEventListener('click', async () => {
    const name = document.getElementById('agent-name').value;
    const model = document.getElementById('agent-model').value;
    const endpoint = document.getElementById('agent-endpoint').value;
    const minComplexity = parseInt(document.getElementById('agent-min-complexity').value);
    const maxComplexity = parseInt(document.getElementById('agent-max-complexity').value);

    if (!name || !model || !endpoint || isNaN(minComplexity) || isNaN(maxComplexity)) {
        showError('Please fill in all required fields');
        return;
    }

    if (minComplexity > maxComplexity) {
        showError('Minimum complexity cannot be greater than maximum complexity');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/agents`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                name,
                model,
                endpoint,
                min_complexity: minComplexity,
                max_complexity: maxComplexity
            })
        });

        if (!response.ok) {
            throw new Error(`Failed to create agent: ${response.status}`);
        }

        const agent = await response.json();

        // Close modal
        createAgentModal.hide();

        // Reset form
        document.getElementById('create-agent-form').reset();

        // Reload agents
        if (dashboardView.style.display !== 'none') {
            loadDashboardData();
        } else if (agentsView.style.display !== 'none') {
            loadAgents();
        }

        // Show success message
        alert('Agent created successfully');
    } catch (error) {
        console.error('Error creating agent:', error);
        showError('Failed to create agent. Please try again.');
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
});
