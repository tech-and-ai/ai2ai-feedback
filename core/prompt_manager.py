"""
Prompt Manager

This module is responsible for generating and managing prompts
for different models and tasks.
"""

import logging
import os
import json
from typing import Dict, List, Optional, Any
from string import Template

from models.task import Task
from models.agent import Agent

logger = logging.getLogger(__name__)

class PromptManager:
    """
    Prompt Manager class for generating and managing prompts.
    """
    
    def __init__(self, prompt_templates_config: Dict[str, Any]):
        """
        Initialize the Prompt Manager.
        
        Args:
            prompt_templates_config: Configuration for prompt templates
        """
        self.prompt_templates_config = prompt_templates_config
        self.prompt_templates = {}
        self._load_prompt_templates()
        logger.info("Prompt Manager initialized")
    
    def _load_prompt_templates(self):
        """
        Load prompt templates from configuration.
        """
        # Load templates from configuration
        for template_name, template_config in self.prompt_templates_config.items():
            if 'content' in template_config:
                self.prompt_templates[template_name] = Template(template_config['content'])
            elif 'file' in template_config:
                file_path = template_config['file']
                try:
                    with open(file_path, 'r') as f:
                        template_content = f.read()
                    self.prompt_templates[template_name] = Template(template_content)
                except Exception as e:
                    logger.error(f"Error loading prompt template from file {file_path}: {e}")
    
    async def generate_prompt(self, 
                             template_name: str, 
                             task: Task, 
                             agent: Agent,
                             additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a prompt using a template.
        
        Args:
            template_name: Template name
            task: Task for which to generate the prompt
            agent: Agent for which to generate the prompt
            additional_context: Additional context for the prompt
            
        Returns:
            Generated prompt
        """
        if template_name not in self.prompt_templates:
            logger.error(f"Prompt template not found: {template_name}")
            raise ValueError(f"Prompt template not found: {template_name}")
        
        template = self.prompt_templates[template_name]
        
        # Prepare context for template
        context = {
            'task_id': task.id,
            'task_title': task.title,
            'task_description': task.description,
            'task_status': task.status.value,
            'task_priority': task.priority.value,
            'agent_id': agent.id,
            'agent_name': agent.name,
            'agent_model': agent.model,
        }
        
        # Add task metadata
        for key, value in task.metadata.items():
            context[f'task_metadata_{key}'] = value
        
        # Add agent capabilities
        for key, value in agent.capabilities.items():
            context[f'agent_capability_{key}'] = value
        
        # Add additional context
        if additional_context:
            context.update(additional_context)
        
        # Generate prompt
        try:
            prompt = template.substitute(context)
            return prompt
        except KeyError as e:
            logger.error(f"Missing key in prompt template {template_name}: {e}")
            raise ValueError(f"Missing key in prompt template {template_name}: {e}")
    
    async def generate_system_prompt(self, 
                                    agent: Agent, 
                                    task: Task,
                                    additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a system prompt for an agent.
        
        Args:
            agent: Agent for which to generate the system prompt
            task: Task for which to generate the system prompt
            additional_context: Additional context for the prompt
            
        Returns:
            Generated system prompt
        """
        # Determine the appropriate system prompt template based on agent and task
        template_name = self._get_system_prompt_template(agent, task)
        
        return await self.generate_prompt(template_name, task, agent, additional_context)
    
    def _get_system_prompt_template(self, agent: Agent, task: Task) -> str:
        """
        Get the appropriate system prompt template for an agent and task.
        
        Args:
            agent: Agent for which to get the system prompt template
            task: Task for which to get the system prompt template
            
        Returns:
            System prompt template name
        """
        # Check if there's a specific template for this agent and task
        agent_task_template = f"system_{agent.id}_{task.id}"
        if agent_task_template in self.prompt_templates:
            return agent_task_template
        
        # Check if there's a specific template for this agent
        agent_template = f"system_{agent.id}"
        if agent_template in self.prompt_templates:
            return agent_template
        
        # Check if there's a specific template for this model
        model_template = f"system_{agent.model}"
        if model_template in self.prompt_templates:
            return model_template
        
        # Check if there's a specific template for this task
        task_template = f"system_{task.id}"
        if task_template in self.prompt_templates:
            return task_template
        
        # Fall back to default system prompt
        return "system_default"
    
    async def generate_task_prompt(self, 
                                  task: Task, 
                                  agent: Agent,
                                  stage: str,
                                  additional_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a prompt for a specific task stage.
        
        Args:
            task: Task for which to generate the prompt
            agent: Agent for which to generate the prompt
            stage: Task stage (e.g., 'planning', 'execution', 'review')
            additional_context: Additional context for the prompt
            
        Returns:
            Generated prompt
        """
        # Determine the appropriate prompt template based on agent, task, and stage
        template_name = self._get_task_prompt_template(agent, task, stage)
        
        return await self.generate_prompt(template_name, task, agent, additional_context)
    
    def _get_task_prompt_template(self, agent: Agent, task: Task, stage: str) -> str:
        """
        Get the appropriate task prompt template for an agent, task, and stage.
        
        Args:
            agent: Agent for which to get the task prompt template
            task: Task for which to get the task prompt template
            stage: Task stage
            
        Returns:
            Task prompt template name
        """
        # Check if there's a specific template for this agent, task, and stage
        agent_task_stage_template = f"{stage}_{agent.id}_{task.id}"
        if agent_task_stage_template in self.prompt_templates:
            return agent_task_stage_template
        
        # Check if there's a specific template for this agent and stage
        agent_stage_template = f"{stage}_{agent.id}"
        if agent_stage_template in self.prompt_templates:
            return agent_stage_template
        
        # Check if there's a specific template for this model and stage
        model_stage_template = f"{stage}_{agent.model}"
        if model_stage_template in self.prompt_templates:
            return model_stage_template
        
        # Check if there's a specific template for this task and stage
        task_stage_template = f"{stage}_{task.id}"
        if task_stage_template in self.prompt_templates:
            return task_stage_template
        
        # Fall back to default stage prompt
        return f"{stage}_default"
