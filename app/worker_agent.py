"""
Worker Agent for AI-to-AI Feedback API

This module implements a specialized worker agent that:
1. Processes assigned tasks using LLM intelligence
2. Reports progress
3. Handles task completion
4. Creates artifacts and documentation
5. Manages the workflow between different agent roles
"""

import os
import json
import logging
import asyncio
import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_, func, desc, text

from .database import Task, Agent, TaskContext, TaskUpdate, async_session, get_db
from .providers.factory import get_model_provider
from .tools.file_operations import FileOperations
from .tools.shell_commands import ShellCommands
from .task_management import ContextScaffold

# Configure logging
logger = logging.getLogger("worker-agent")

class WorkerAgent:
    """
    Worker agent that processes tasks
    """

    def __init__(self, agent_id: str, name: str, role: str, model: str, skills: List[str], endpoint: str = None):
        """
        Initialize a worker agent

        Args:
            agent_id: Agent ID
            name: Agent name
            role: Agent role
            model: AI model to use
            skills: List of skills
            endpoint: Ollama endpoint URL
        """
        self.agent_id = agent_id
        self.name = name
        self.role = role
        self.model = model
        self.skills = skills
        self.status = "idle"
        self.endpoint = endpoint
        # Set agent ID in environment for load balancing
        os.environ["AGENT_ID"] = self.agent_id

        # Initialize provider with load balancing and custom endpoint
        self.provider = get_model_provider("ollama", self.model)

        # If endpoint is provided, update the provider's endpoint
        if self.endpoint:
            self.provider.endpoint = self.endpoint if self.endpoint.startswith("http") else f"http://{self.endpoint}"

        # Create workspace
        self.workspace = FileOperations.get_agent_workspace(agent_id, self.name, self.role)

    async def start(self):
        """Start the worker agent"""
        self.running = True
        self.status = "running"
        logger.info(f"Worker Agent {self.name} ({self.agent_id}) started")

        # Start the task monitoring loop
        asyncio.create_task(self._task_loop())
        return True

    async def stop(self):
        """Stop the worker agent"""
        self.running = False
        self.status = "stopped"
        logger.info(f"Worker Agent {self.name} ({self.agent_id}) stopped")
        return True

    async def _task_loop(self):
        """Monitor tasks and process them"""
        while self.running:
            try:
                # Get database session
                db_gen = get_db()
                db = await anext(db_gen)

                # Look for assigned tasks
                await self._process_assigned_tasks(db)

                # Sleep before next check
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(30)

    async def _process_assigned_tasks(self, db: AsyncSession):
        """Process tasks assigned to this agent"""
        try:
            # Find tasks assigned to this agent
            query = select(Task).where(
                Task.status == "in_progress",
                Task.assigned_to == self.agent_id
            )

            result = await db.execute(query)
            tasks = result.scalars().all()

            for task in tasks:
                # Process the task
                logger.info(f"Processing task: {task.id} - {task.title}")
                await self._process_task(db, task)
        except Exception as e:
            logger.error(f"Error processing assigned tasks: {e}")

    async def _process_task(self, db: AsyncSession, task: Task):
        """Process a task using LLM intelligence and create follow-up tasks based on role"""
        try:
            # Update task progress
            task.progress = 25
            await db.commit()

            # Add update about starting the task
            await ContextScaffold.add_task_update(
                db,
                task.id,
                self.agent_id,
                f"Starting work on task: {task.title}. Analyzing requirements and planning approach."
            )

            # Get task context
            task_context = await ContextScaffold.get_task_context(db, task.id)

            # Build prompt based on agent role
            system_prompt = await self._build_system_prompt(task, self.role)
            user_prompt = await self._build_user_prompt(task, task_context)

            # Call LLM to process the task
            logger.info(f"Calling LLM ({self.model}) to process task: {task.id}")

            # Update progress
            task.progress = 50
            await db.commit()
            await ContextScaffold.add_task_update(
                db,
                task.id,
                self.agent_id,
                f"Working on task: {task.title}. Progress: 50%"
            )

            # Generate response using LLM
            try:
                # No fallback - if LLM fails, the task fails
                llm_response = await self.provider.generate_completion(system_prompt, user_prompt)
                logger.info(f"Received LLM response for task: {task.id} (length: {len(llm_response)})")

                # Process the LLM response
                result, artifacts = await self._process_llm_response(task, llm_response)

                # Save artifacts to workspace if any
                if artifacts:
                    for filename, content in artifacts.items():
                        success, message = FileOperations.write_file(
                            self.agent_id,
                            filename,
                            content
                        )
                        if success:
                            logger.info(f"Saved artifact: {filename}")
                            await ContextScaffold.add_task_update(
                                db,
                                task.id,
                                self.agent_id,
                                f"Created artifact: {filename}"
                            )
                        else:
                            logger.error(f"Failed to save artifact {filename}: {message}")

                # Complete the task
                task.status = "completed"
                task.progress = 100
                task.completed_at = datetime.utcnow()
                task.result = result

                # Create follow-up task based on role
                if self.role == "Designer":
                    await self._create_development_task(db, task)
                elif self.role == "Developer":
                    await self._create_testing_task(db, task)
                elif self.role == "Tester":
                    await self._create_review_task(db, task)
                # No follow-up task for Reviewer

                await db.commit()

                # Add update about completion
                await ContextScaffold.add_task_update(
                    db,
                    task.id,
                    self.agent_id,
                    f"Task completed: {task.title}. Result summary: {result[:200]}..."
                )

                logger.info(f"Task completed: {task.id} - {task.title}")

            except Exception as llm_error:
                logger.error(f"LLM processing error for task {task.id}: {llm_error}")

                # Mark the task as failed
                task.status = "failed"
                task.progress = 0
                task.result = f"Failed due to LLM error: {str(llm_error)}"
                await db.commit()

                await ContextScaffold.add_task_update(
                    db,
                    task.id,
                    self.agent_id,
                    f"Task failed: Error processing with LLM: {str(llm_error)}"
                )

                logger.info(f"Task {task.id} marked as failed due to LLM error")
                raise llm_error

        except Exception as e:
            logger.error(f"Error processing task {task.id}: {e}")

            # Mark the task as failed
            task.status = "failed"
            task.progress = 0
            task.result = f"Failed due to error: {str(e)}"
            await db.commit()

            # Add update about error
            await ContextScaffold.add_task_update(
                db,
                task.id,
                self.agent_id,
                f"Task failed: Error processing task: {str(e)}"
            )

            logger.info(f"Task {task.id} marked as failed due to processing error")

    async def _create_development_task(self, db: AsyncSession, design_task: Task):
        """Create a development task after design is complete"""
        try:
            # Get the project
            query = select(Task).where(
                Task.id == design_task.project_id
            )
            result = await db.execute(query)
            project = result.scalars().first()

            if not project:
                logger.error(f"Project not found for design task: {design_task.id}")
                return

            # Create a development task
            dev_task = Task(
                id=str(uuid.uuid4()),
                title=f"Implementation for {project.title}",
                description=f"Implement the code according to the design specifications: {design_task.result}",
                status="pending",
                created_by=self.agent_id,
                project_id=project.id,
                task_type="development",
                required_skills="python,javascript,development,backend,frontend",
                priority=project.priority,
                estimated_effort=12
            )
            db.add(dev_task)
            await db.commit()

            # Add update about task creation
            await ContextScaffold.add_task_update(
                db,
                project.id,
                self.agent_id,
                f"Design phase completed. Created development task for implementation."
            )

            logger.info(f"Created development task: {dev_task.id} for project: {project.id}")
        except Exception as e:
            logger.error(f"Error creating development task: {e}")

    async def _create_testing_task(self, db: AsyncSession, dev_task: Task):
        """Create a testing task after development is complete"""
        try:
            # Get the project
            query = select(Task).where(
                Task.id == dev_task.project_id
            )
            result = await db.execute(query)
            project = result.scalars().first()

            if not project:
                logger.error(f"Project not found for development task: {dev_task.id}")
                return

            # Create a testing task
            test_task = Task(
                id=str(uuid.uuid4()),
                title=f"Testing for {project.title}",
                description=f"Test the implementation to ensure it meets requirements: {dev_task.result}",
                status="pending",
                created_by=self.agent_id,
                project_id=project.id,
                task_type="testing",
                required_skills="testing,quality,python,javascript",
                priority=project.priority,
                estimated_effort=8
            )
            db.add(test_task)
            await db.commit()

            # Add update about task creation
            await ContextScaffold.add_task_update(
                db,
                project.id,
                self.agent_id,
                f"Development phase completed. Created testing task for verification."
            )

            logger.info(f"Created testing task: {test_task.id} for project: {project.id}")
        except Exception as e:
            logger.error(f"Error creating testing task: {e}")

    async def _create_review_task(self, db: AsyncSession, test_task: Task):
        """Create a review task after testing is complete"""
        try:
            # Get the project
            query = select(Task).where(
                Task.id == test_task.project_id
            )
            result = await db.execute(query)
            project = result.scalars().first()

            if not project:
                logger.error(f"Project not found for testing task: {test_task.id}")
                return

            # Create a review task
            review_task = Task(
                id=str(uuid.uuid4()),
                title=f"Review for {project.title}",
                description=f"Review the implementation and test results: {test_task.result}",
                status="pending",
                created_by=self.agent_id,
                project_id=project.id,
                task_type="review",
                required_skills="review,quality,documentation",
                priority=project.priority,
                estimated_effort=4
            )
            db.add(review_task)
            await db.commit()

            # Add update about task creation
            await ContextScaffold.add_task_update(
                db,
                project.id,
                self.agent_id,
                f"Testing phase completed. Created review task for final approval."
            )

            logger.info(f"Created review task: {review_task.id} for project: {project.id}")
        except Exception as e:
            logger.error(f"Error creating review task: {e}")

    async def _build_system_prompt(self, task: Task, role: str) -> str:
        """Build a system prompt based on the agent's role"""
        base_prompt = f"You are an AI assistant specialized in {role.lower()} tasks. "

        if role == "Designer":
            return base_prompt + """
You are a skilled software architect and designer. Your task is to analyze requirements and create detailed design specifications.

Your responsibilities include:
1. Analyzing project requirements thoroughly
2. Creating architecture diagrams (describe them in detail)
3. Designing data models with field specifications
4. Defining API specifications with endpoints, methods, request/response formats
5. Outlining component interactions and dependencies
6. Considering security, scalability, and performance aspects

Provide your design in a structured format with clear sections for:
- Architecture Overview
- Data Models
- API Specifications
- Component Interactions
- Security Considerations
- Implementation Recommendations

Be thorough and detailed in your specifications to guide the development team.
"""
        elif role == "Developer":
            return base_prompt + """
You are an expert software developer. Your task is to implement code based on design specifications.

Your responsibilities include:
1. Implementing code according to design specifications
2. Following best practices and coding standards
3. Ensuring code is efficient, maintainable, and secure
4. Documenting your code with clear comments
5. Implementing error handling and edge cases
6. Creating unit tests for your code

Provide your implementation in a structured format with:
- Implementation Overview
- Code Files (with full code)
- Testing Approach
- Installation/Setup Instructions
- Usage Examples
- Known Limitations

Your code should be production-ready and well-documented.
"""
        elif role == "Tester":
            return base_prompt + """
You are a skilled quality assurance engineer. Your task is to test implementations to ensure they meet requirements.

Your responsibilities include:
1. Creating comprehensive test plans
2. Writing test cases covering functionality, edge cases, and error handling
3. Implementing automated tests where appropriate
4. Performing manual testing for user experience
5. Identifying and documenting bugs or issues
6. Verifying that the implementation meets the original requirements

Provide your testing results in a structured format with:
- Test Summary
- Test Cases (with expected and actual results)
- Issues Found (if any)
- Test Coverage Analysis
- Recommendations for Improvement
- Overall Assessment

Be thorough in your testing to ensure high-quality deliverables.
"""
        elif role == "Reviewer":
            return base_prompt + """
You are an experienced code reviewer and quality assurance specialist. Your task is to review implementations and test results.

Your responsibilities include:
1. Reviewing code for quality, maintainability, and adherence to best practices
2. Assessing test coverage and test quality
3. Verifying that the implementation meets the original requirements
4. Identifying potential issues, bugs, or security vulnerabilities
5. Providing constructive feedback for improvement
6. Making a final recommendation on whether the implementation is ready for deployment

Provide your review in a structured format with:
- Review Summary
- Code Quality Assessment
- Test Coverage Assessment
- Requirements Fulfillment
- Issues and Recommendations
- Final Verdict

Be thorough but fair in your assessment, focusing on constructive feedback.
"""
        else:
            # Generic prompt for other roles
            return base_prompt + """
Your task is to analyze the given problem and provide a comprehensive solution.

Provide your response in a structured format with clear sections for:
- Analysis
- Solution
- Implementation Details
- Recommendations

Be thorough and detailed in your response.
"""

    async def _build_user_prompt(self, task: Task, task_context: Dict[str, Any]) -> str:
        """Build a user prompt with task details and context"""
        prompt = f"""
# Task: {task.title}

## Description
{task.description}

## Task ID
{task.id}

"""

        # Add parent task information if available
        if task_context.get("parent"):
            parent = task_context["parent"]
            prompt += f"""
## Parent Task
Title: {parent.get('title')}
Description: {parent.get('description')}
Result: {parent.get('result')}

"""

        # Add context entries if available
        if task_context.get("context_entries") and len(task_context["context_entries"]) > 0:
            prompt += "## Additional Context\n"
            for key, value in task_context["context_entries"].items():
                prompt += f"### {key}\n{value}\n\n"

        # Add recent updates if available
        if task_context.get("updates") and len(task_context["updates"]) > 0:
            prompt += "## Recent Updates\n"
            # Only include the last 5 updates to avoid context bloat
            for update in task_context["updates"][-5:]:
                prompt += f"- {update.get('timestamp', '')}: {update.get('content', '')}\n"

        # Add subtasks if available
        if task_context.get("subtasks") and len(task_context["subtasks"]) > 0:
            prompt += "## Related Subtasks\n"
            for subtask in task_context["subtasks"]:
                prompt += f"- {subtask.get('title')} (Status: {subtask.get('status')})\n"

        # Add instructions based on task type
        if task.task_type == "design":
            prompt += """
## Instructions
Please create a comprehensive design document based on the requirements above.
Include architecture diagrams, data models, API specifications, and implementation recommendations.
Your design should be detailed enough to guide the development team.
"""
        elif task.task_type == "development":
            prompt += """
## Instructions
Please implement the code based on the design specifications above.
Include all necessary files, documentation, and tests.
Your code should be production-ready and follow best practices.
"""
        elif task.task_type == "testing":
            prompt += """
## Instructions
Please create and execute a comprehensive test plan for the implementation.
Include test cases, test results, and any issues found.
Your testing should verify that the implementation meets the requirements.
"""
        elif task.task_type == "review":
            prompt += """
## Instructions
Please review the implementation and test results.
Assess code quality, test coverage, and requirements fulfillment.
Provide constructive feedback and a final recommendation.
"""

        # Final instruction
        prompt += """
## Output Format
Please provide your response in a structured format with clear sections.
Include any code, diagrams, or other artifacts as needed.
Be thorough and detailed in your response.
"""

        return prompt

    async def _process_llm_response(self, task: Task, llm_response: str) -> Tuple[str, Dict[str, str]]:
        """
        Process the LLM response to extract the result and any artifacts

        Args:
            task: The task being processed
            llm_response: The raw response from the LLM

        Returns:
            Tuple[str, Dict[str, str]]: (Result summary, Dictionary of artifacts)
        """
        # Initialize artifacts dictionary
        artifacts = {}

        # Extract code blocks and save as artifacts
        code_blocks = self._extract_code_blocks(llm_response)
        for i, (language, code) in enumerate(code_blocks):
            if language and code:
                # Determine file extension based on language
                extension = self._get_file_extension(language)

                # Create filename
                if task.task_type == "design":
                    prefix = "design"
                elif task.task_type == "development":
                    prefix = "implementation"
                elif task.task_type == "testing":
                    prefix = "test"
                elif task.task_type == "review":
                    prefix = "review"
                else:
                    prefix = "output"

                # Create a unique filename
                filename = f"{prefix}_{i+1}{extension}"

                # Add to artifacts
                artifacts[filename] = code

        # Create a summary document with the full response
        summary_filename = f"{task.task_type}_summary.md"
        artifacts[summary_filename] = llm_response

        # Extract a brief summary for the task result
        summary = self._extract_summary(llm_response, task.task_type)

        return summary, artifacts

    def _extract_code_blocks(self, text: str) -> List[Tuple[str, str]]:
        """
        Extract code blocks from markdown text

        Args:
            text: Markdown text containing code blocks

        Returns:
            List[Tuple[str, str]]: List of (language, code) tuples
        """
        import re

        # Pattern to match markdown code blocks
        pattern = r"```(\w*)\n(.*?)```"

        # Find all code blocks
        matches = re.findall(pattern, text, re.DOTALL)

        return matches

    def _get_file_extension(self, language: str) -> str:
        """
        Get file extension based on language

        Args:
            language: Programming language

        Returns:
            str: File extension
        """
        language = language.lower()

        # Map of languages to file extensions
        extensions = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "html": ".html",
            "css": ".css",
            "json": ".json",
            "markdown": ".md",
            "md": ".md",
            "sql": ".sql",
            "bash": ".sh",
            "shell": ".sh",
            "java": ".java",
            "c": ".c",
            "cpp": ".cpp",
            "csharp": ".cs",
            "go": ".go",
            "ruby": ".rb",
            "php": ".php",
            "rust": ".rs",
            "swift": ".swift",
            "kotlin": ".kt",
            "": ".txt"  # Default for empty language
        }

        return extensions.get(language, ".txt")



    def _extract_summary(self, text: str, task_type: str) -> str:
        """
        Extract a summary from the LLM response

        Args:
            text: LLM response text
            task_type: Type of task

        Returns:
            str: Summary text
        """
        # Look for specific sections based on task type
        import re

        if task_type == "design":
            # Look for Architecture Overview or Summary section
            pattern = r"(?:Architecture Overview|Summary|Executive Summary)[:\n]+(.*?)(?:\n#|\n##|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        elif task_type == "development":
            # Look for Implementation Overview or Summary section
            pattern = r"(?:Implementation Overview|Summary|Implementation Summary)[:\n]+(.*?)(?:\n#|\n##|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        elif task_type == "testing":
            # Look for Test Summary section
            pattern = r"(?:Test Summary|Testing Summary|Summary)[:\n]+(.*?)(?:\n#|\n##|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        elif task_type == "review":
            # Look for Review Summary or Final Verdict section
            pattern = r"(?:Review Summary|Final Verdict|Summary)[:\n]+(.*?)(?:\n#|\n##|$)"
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # If no specific section found, use the first paragraph
        paragraphs = text.split("\n\n")
        for paragraph in paragraphs:
            if paragraph and not paragraph.startswith("#") and len(paragraph) > 50:
                return paragraph.strip()

        # Fallback to first 200 characters
        return text[:200].strip() + "..."
