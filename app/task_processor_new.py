import os
import time
import uuid
import json
import logging
import sqlite3
import requests
import subprocess
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("task_processor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("task-processor")

# Database path
DB_PATH = os.getenv("DB_PATH", "ai2ai_feedback.db")

# Ollama endpoint
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434/api/generate")

# Fallback models
fallback_models = {
    "gemma3:4b": "gemma3:1b",
    "gemma3:1b": None,
    "deepseek-coder-v2-16b": None
}

class TaskProcessor:
    def __init__(self):
        """Initialize the task processor."""
        self.conn = None
        self.cursor = None
        self.connect_db()

    def connect_db(self):
        """Connect to the SQLite database."""
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def get_next_task(self):
        """Get the next available task from the queue.
        
        First, check for tasks with a specific assigned_agent_id.
        If none found, get the next task based on priority and creation time.
        """
        # First, check for tasks with a specific assigned_agent_id
        self.cursor.execute(
            'SELECT t.*, a.id as agent_id FROM tasks t JOIN agents a ON t.assigned_agent_id = a.id WHERE t.status = "not_started" AND a.status = "available" ORDER BY t.priority DESC, t.created_at ASC LIMIT 1'
        )
        task = self.cursor.fetchone()
        
        if task:
            logger.info(f"Found task {task['id']} with pre-assigned agent {task['agent_id']}")
            return task
        
        # If no tasks with assigned_agent_id, get the next task based on priority and creation time
        self.cursor.execute(
            'SELECT * FROM tasks WHERE status = "not_started" AND (assigned_agent_id IS NULL OR assigned_agent_id = "") ORDER BY priority DESC, created_at ASC LIMIT 1'
        )
        return self.cursor.fetchone()

    def get_available_agent(self, task_complexity):
        """Get an available agent that can handle the task complexity."""
        self.cursor.execute(
            'SELECT * FROM agents WHERE status = "available" AND min_complexity <= ? AND max_complexity >= ? LIMIT 1',
            (task_complexity, task_complexity)
        )
        return self.cursor.fetchone()

    def assign_task_to_agent(self, task_id, agent_id):
        """Assign a task to an agent and update statuses."""
        try:
            # Update task
            self.cursor.execute(
                'UPDATE tasks SET assigned_agent_id = ?, status = "design", updated_at = ? WHERE id = ?',
                (agent_id, datetime.now().isoformat(), task_id)
            )

            # Update agent
            self.cursor.execute(
                'UPDATE agents SET status = "busy", last_active = ? WHERE id = ?',
                (datetime.now().isoformat(), agent_id)
            )

            # Generate a unique ID for the task update
            update_id = str(uuid.uuid4())

            # Create task update
            self.cursor.execute(
                'INSERT INTO task_updates (id, task_id, agent_id, update_type, content, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
                (update_id, task_id, agent_id, "status_change", f"Task assigned to agent {agent_id} and moved to design stage", datetime.now().isoformat())
            )

            self.conn.commit()
            logger.info(f"Task {task_id} assigned to agent {agent_id}")
            return True
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error assigning task: {e}")
            return False

    def run(self, interval=15):
        """
        Main loop to continuously process tasks.

        Args:
            interval: Time in seconds to wait between checking for new tasks
        """
        logger.info("Starting task processor")

        try:
            while True:
                try:
                    # Reconnect to the database if needed
                    if self.conn is None:
                        self.connect_db()

                    # Get next task
                    task = self.get_next_task()

                    if task:
                        logger.info(f"Found task: {task['id']} - {task['title']}")

                        # Check if task already has an assigned agent
                        if 'agent_id' in task:
                            # Task has a pre-assigned agent that is available
                            agent_id = task['agent_id']
                            
                            # Get the agent details
                            self.cursor.execute(
                                'SELECT * FROM agents WHERE id = ?',
                                (agent_id,)
                            )
                            agent = self.cursor.fetchone()
                            
                            logger.info(f"Using pre-assigned agent: {agent['id']} - {agent['name']}")
                        else:
                            # Get available agent
                            agent = self.get_available_agent(task['complexity'])

                            if not agent:
                                logger.info(f"No available agent for task {task['id']} (complexity: {task['complexity']})")
                                # Wait for next check
                                logger.info(f"Waiting {interval} seconds before next check")
                                time.sleep(interval)
                                continue

                            logger.info(f"Found available agent: {agent['id']} - {agent['name']}")

                        # Assign task to agent
                        if self.assign_task_to_agent(task['id'], agent['id']):
                            # Process task with timeout
                            try:
                                # Set a timeout for task processing
                                max_processing_time = 1800  # 30 minutes
                                start_time = time.time()

                                # Process the task
                                self.process_task(task, agent)

                                # Check if processing took too long
                                if time.time() - start_time > max_processing_time:
                                    logger.warning(f"Task {task['id']} processing took too long, may be stuck")
                            except Exception as e:
                                logger.error(f"Error processing task {task['id']}: {e}")
                                # Reset task and agent status
                                self.update_task_status(task['id'], "not_started", 0, f"Task processing failed: {str(e)}", agent['id'])
                                self.cursor.execute(
                                    'UPDATE agents SET status = "available", last_active = ? WHERE id = ?',
                                    (datetime.now().isoformat(), agent['id'])
                                )
                                self.conn.commit()
                    else:
                        logger.info("No tasks in queue")

                    # Check if there are any stuck agents
                    self.cursor.execute(
                        'SELECT * FROM agents WHERE status = "busy"'
                    )
                    busy_agents = self.cursor.fetchall()

                    for busy_agent in busy_agents:
                        # Check when the agent was last active
                        last_active = datetime.fromisoformat(busy_agent['last_active'])
                        now = datetime.now()

                        # If the agent has been busy for more than 30 minutes, reset it
                        if (now - last_active).total_seconds() > 1800:  # 30 minutes
                            logger.warning(f"Agent {busy_agent['id']} has been busy for too long, resetting")

                            # Get the task assigned to this agent
                            self.cursor.execute(
                                'SELECT * FROM tasks WHERE assigned_agent_id = ?',
                                (busy_agent['id'],)
                            )
                            stuck_task = self.cursor.fetchone()

                            if stuck_task:
                                # Reset the task
                                self.update_task_status(stuck_task['id'], "not_started", 0, "Task reset due to timeout", busy_agent['id'])

                            # Reset the agent
                            self.cursor.execute(
                                'UPDATE agents SET status = "available", last_active = ? WHERE id = ?',
                                (datetime.now().isoformat(), busy_agent['id'])
                            )
                            self.conn.commit()

                    # Wait for next check
                    logger.info(f"Waiting {interval} seconds before next check")
                    time.sleep(interval)

                except sqlite3.Error as e:
                    logger.error(f"Database error: {e}")
                    # Try to reconnect to the database
                    self.close_db()
                    time.sleep(5)
                    self.connect_db()
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Task processor stopped by user")
        except Exception as e:
            logger.error(f"Task processor error: {e}")
        finally:
            self.close_db()
            logger.info("Task processor stopped")
