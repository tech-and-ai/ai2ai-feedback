"""
Output Processor

This module is responsible for processing, validating, and storing
model outputs.
"""

import logging
import uuid
import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from models.output import Output, OutputType
from models.task import Task
from models.agent import Agent

logger = logging.getLogger(__name__)

class OutputProcessor:
    """
    Output Processor class for processing, validating, and storing outputs.
    """

    def __init__(self, db_connection):
        """
        Initialize the Output Processor.

        Args:
            db_connection: Database connection
        """
        self.db = db_connection
        self.validators = self._initialize_validators()
        self.output_dir = os.environ.get('OUTPUT_DIR', 'outputs')

        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info("Output Processor initialized")

    def _initialize_validators(self) -> Dict[str, Any]:
        """
        Initialize output validators.

        Returns:
            Dictionary of validators
        """
        validators = {
            OutputType.TEXT.value: self._validate_text,
            OutputType.CODE.value: self._validate_code,
            OutputType.HTML.value: self._validate_html,
            OutputType.JSON.value: self._validate_json,
            OutputType.MARKDOWN.value: self._validate_markdown,
        }

        return validators

    async def process_output(self,
                            task: Task,
                            agent: Agent,
                            content: str,
                            output_type: OutputType,
                            metadata: Optional[Dict[str, Any]] = None) -> Output:
        """
        Process, validate, and store an output.

        Args:
            task: Task for which the output was generated
            agent: Agent that generated the output
            content: Output content
            output_type: Output type
            metadata: Additional output metadata

        Returns:
            Processed output
        """
        # Validate output
        is_valid, validation_message = await self.validate_output(content, output_type)

        if not is_valid:
            logger.warning(f"Invalid output of type {output_type.value}: {validation_message}")

        # Create output
        output_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        output = Output(
            id=output_id,
            task_id=task.id,
            agent_id=agent.id,
            type=output_type,
            content=content,
            created_at=now,
            metadata=metadata or {}
        )

        # Save output to database
        await self.db.outputs.create(output)

        # Save output to file
        await self._save_output_to_file(output)

        logger.info(f"Processed output {output_id} for task {task.id}")
        return output

    async def validate_output(self, content: str, output_type: OutputType) -> tuple[bool, str]:
        """
        Validate an output.

        Args:
            content: Output content
            output_type: Output type

        Returns:
            Tuple of (is_valid, validation_message)
        """
        validator = self.validators.get(output_type.value)

        if not validator:
            logger.warning(f"No validator found for output type: {output_type.value}")
            return True, "No validator available"

        return await validator(content)

    async def _validate_text(self, content: str) -> tuple[bool, str]:
        """
        Validate text output.

        Args:
            content: Output content

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not content:
            return False, "Empty content"

        return True, "Valid text output"

    async def _validate_code(self, content: str) -> tuple[bool, str]:
        """
        Validate code output.

        Args:
            content: Output content

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not content:
            return False, "Empty content"

        # Basic validation - check for common syntax errors
        if content.count('{') != content.count('}'):
            return False, "Mismatched braces"

        if content.count('(') != content.count(')'):
            return False, "Mismatched parentheses"

        if content.count('[') != content.count(']'):
            return False, "Mismatched brackets"

        return True, "Valid code output"

    async def _validate_html(self, content: str) -> tuple[bool, str]:
        """
        Validate HTML output.

        Args:
            content: Output content

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not content:
            return False, "Empty content"

        # Basic validation - check for common HTML elements
        if '<html' not in content.lower():
            return False, "Missing <html> tag"

        if '<body' not in content.lower():
            return False, "Missing <body> tag"

        return True, "Valid HTML output"

    async def _validate_json(self, content: str) -> tuple[bool, str]:
        """
        Validate JSON output.

        Args:
            content: Output content

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not content:
            return False, "Empty content"

        try:
            json.loads(content)
            return True, "Valid JSON output"
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e}"

    async def _validate_markdown(self, content: str) -> tuple[bool, str]:
        """
        Validate Markdown output.

        Args:
            content: Output content

        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not content:
            return False, "Empty content"

        return True, "Valid Markdown output"

    async def _save_output_to_file(self, output: Output) -> str:
        """
        Save output to a file.

        Args:
            output: Output to save

        Returns:
            File path
        """
        # Create task directory if it doesn't exist
        task_dir = os.path.join(self.output_dir, output.task_id)
        os.makedirs(task_dir, exist_ok=True)

        # Determine file extension
        extension = self._get_file_extension(output.type)

        # Create file name
        file_name = f"{output.id}{extension}"
        file_path = os.path.join(task_dir, file_name)

        # Write output to file
        with open(file_path, 'w') as f:
            f.write(output.content)

        logger.info(f"Saved output to file: {file_path}")
        return file_path

    def _get_file_extension(self, output_type: OutputType) -> str:
        """
        Get file extension for an output type.

        Args:
            output_type: Output type

        Returns:
            File extension
        """
        extensions = {
            OutputType.TEXT.value: '.txt',
            OutputType.CODE.value: '.code',
            OutputType.HTML.value: '.html',
            OutputType.JSON.value: '.json',
            OutputType.MARKDOWN.value: '.md',
        }

        # Handle both enum and string values
        if isinstance(output_type, OutputType):
            type_value = output_type.value
        else:
            type_value = output_type

        return extensions.get(type_value, '.txt')
