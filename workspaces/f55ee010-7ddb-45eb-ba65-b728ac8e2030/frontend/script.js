
document.addEventListener('DOMContentLoaded', () => {
    const taskList = document.getElementById('task-list').querySelector('ul');
    const taskForm = document.getElementById('task-form');

    // Function to fetch tasks from the API
    async function fetchTasks() {
        try {
            const response = await fetch('http://localhost:8000/tasks'); // Replace with your API endpoint
            const tasks = await response.json();

            // Clear existing task list
            taskList.innerHTML = '';

            // Add each task to the list
            tasks.forEach(task => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <strong>${task.title}</strong><br>
                    ${task.description ? task.description + '<br>' : ''}
                    Due Date: ${task.due_date ? task.due_date + '<br>' : 'N/A'}<br>
                    Status: ${task.status}<br>
                    <button onclick="updateTaskStatus(${task.id}, 'completed')">Mark Complete</button>
                    <button onclick="deleteTask(${task.id})">Delete</button>
                `;
                taskList.appendChild(listItem);
            });
        } catch (error) {
            console.error('Error fetching tasks:', error);
        }
    }

    // Function to create a new task
    async function createTask(event) {
        event.preventDefault();

        const title = document.getElementById('title').value;
        const description = document.getElementById('description').value;
        const due_date = document.getElementById('due_date').value;
        const status = document.getElementById('status').value;

        const taskData = {
            title: title,
            description: description,
            due_date: due_date ? due_date : null,
            status: status
        };

        try {
            const response = await fetch('http://localhost:8000/tasks', { // Replace with your API endpoint
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(taskData)
            });

            if (response.ok) {
                // Refresh the task list
                fetchTasks();
                // Clear the form
                taskForm.reset();
            } else {
                console.error('Error creating task:', response.status);
            }
        } catch (error) {
            console.error('Error creating task:', error);
        }
    }

    // Function to update task status (example)
    window.updateTaskStatus = async (taskId, newStatus) => {
        try {
            const response = await fetch(\`http://localhost:8000/tasks/\${taskId}\`, { // Replace with your API endpoint
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ status: newStatus })
            });

            if (response.ok) {
                fetchTasks(); // Refresh the task list
            } else {
                console.error('Error updating task status:', response.status);
            }
        } catch (error) {
            console.error('Error updating task status:', error);
        }
    };

    // Function to delete a task
    window.deleteTask = async (taskId) => {
        try {
            const response = await fetch(\`http://localhost:8000/tasks/\${taskId}\`, { // Replace with your API endpoint
                method: 'DELETE'
            });

            if (response.ok) {
                fetchTasks(); // Refresh the task list
            } else {
                console.error('Error deleting task:', response.status);
            }
        } catch (error) {
            console.error('Error deleting task:', error);
        }
    };

    // Attach event listener to the form
    taskForm.addEventListener('submit', createTask);

    // Initial fetch of tasks
    fetchTasks();
});
