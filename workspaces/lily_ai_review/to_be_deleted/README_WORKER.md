# Worker Process for Research Paper Generation

## Overview

The worker process is responsible for processing research paper generation jobs from the queue. It runs in the background and continuously polls the queue for new jobs, processes them, and updates their status.

## Integration with Main Application

The worker process is automatically started when the main application is launched using the `run.py` script. It runs in a separate thread and is managed by the main application.

## How It Works

1. When the main application starts, it launches the worker process in a separate thread.
2. The worker process polls the queue for new jobs.
3. When a job is found, the worker processes it and updates its status.
4. When the main application exits, it ensures the worker process is terminated gracefully.

## Configuration

The worker process is configured using the following parameters:

- **Poll Interval**: How often the worker checks for new jobs (in seconds). Default: 5 seconds.
- **Max Jobs**: Maximum number of jobs to process in parallel. Default: 1 job.

These parameters can be configured in the database using the `saas_lily_ai_config` table:

- `worker_poll_interval`: Poll interval in seconds
- `worker_max_jobs`: Maximum number of jobs to process in parallel

## Starting the Application

To start both the main application and the worker process, simply run:

```bash
python run.py
```

This will:
1. Kill any existing processes using port 8004
2. Kill any existing main.py or worker_launcher.py processes
3. Start the worker process in a separate thread
4. Start the main application

## Troubleshooting

If you encounter issues with the worker process:

1. Check the logs in `worker.log` for error messages.
2. Check the main application logs in `app.log` for worker-related messages.
3. Verify that the worker process is running by checking the process list:
   ```bash
   ps aux | grep worker_launcher.py
   ```
4. If the application fails to start due to port 8004 being in use:
   ```bash
   sudo lsof -i :8004  # Find processes using port 8004
   sudo kill -9 <PID>  # Kill the process using port 8004
   ```
5. Restart the main application using `run.py` to restart both the main application and the worker process.

## Production Deployment

In a production environment, the worker process is automatically managed by the main application. No additional setup is required.

When deploying to production:

1. Ensure the `run.py` script is used to start the application.
2. Configure the worker parameters in the database as needed for production load.
3. Monitor the worker logs for any issues.
4. Consider setting up a process manager like systemd to ensure the application restarts automatically if it crashes.

### Example systemd Service File

```ini
[Unit]
Description=Lily AI Research Pack Generator
After=network.target

[Service]
User=admin
WorkingDirectory=/path/to/lily_ai
ExecStart=/usr/bin/python /path/to/lily_ai/run.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

## Scaling

To handle increased load, you can adjust the `worker_max_jobs` parameter in the database to process more jobs in parallel. However, be mindful of the server's resources and the LLM API rate limits.
