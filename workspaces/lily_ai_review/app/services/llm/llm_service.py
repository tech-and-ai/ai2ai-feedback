"""
LLM Service for the Lily AI Research Assistant.

This module provides functionality to interact with LLMs through OpenRouter and Requesty.
It ensures that all LLM interactions use the configured model from the database.
"""

import logging
import time
import json
import os
import requests
from typing import Dict, Any, List, Optional, Union

# Import the configuration service
from app.services.config import config_service

# Configure logging
logger = logging.getLogger(__name__)


class LLMService:
    """
    Service for interacting with LLMs through OpenRouter or Requesty.

    This class provides methods to:
    - Generate content using the configured LLM
    - Handle fallback to alternative providers if primary fails
    - Process responses into usable formats
    """

    def __init__(self):
        """Initialize the LLM service with configuration from the database."""
        # Get LLM configuration from the database
        self.default_config = config_service.get_llm_config()
        self.content_config = config_service.get_content_llm_config()
        self.planning_config = config_service.get_planning_llm_config()
        self.research_config = config_service.get_research_llm_config()

        # Get API keys from environment variables
        self.openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
        self.requesty_api_key = os.environ.get("REQUESTY_API_KEY")

        # Log the configuration
        logger.info(f"LLM Service initialized with model: {self.default_config['model']}")
        logger.info(f"Primary provider: {self.default_config['provider']}")
        logger.info(f"Fallback provider: {self.default_config['fallback_provider']}")

    def generate_content(self,
                         prompt: str,
                         config_type: str = 'default',
                         max_tokens: Optional[int] = None,
                         system_prompt: Optional[str] = None) -> str:
        """
        Generate content using the configured LLM.

        Args:
            prompt: The prompt to send to the LLM
            config_type: The type of configuration to use ('default', 'content', 'planning', 'research')
            max_tokens: Override the max tokens setting from the configuration
            system_prompt: Optional system prompt to use

        Returns:
            The generated content as a string
        """
        # Get the appropriate configuration
        if config_type == 'content':
            config = self.content_config
        elif config_type == 'planning':
            config = self.planning_config
        elif config_type == 'research':
            config = self.research_config
        else:
            config = self.default_config

        # Override max tokens if provided
        if max_tokens is not None:
            config = config.copy()
            config['max_tokens'] = max_tokens

        # Log the request
        logger.info(f"Generating content with {config['model']} via {config['provider']}")
        logger.debug(f"Prompt: {prompt[:100]}...")

        try:
            # Try the primary provider first
            return self._generate_with_provider(prompt, config, config['provider'], system_prompt)
        except Exception as e:
            # Log the error and try the fallback provider
            logger.error(f"Error with primary provider {config['provider']}: {str(e)}")
            logger.info(f"Falling back to {config['fallback_provider']}")

            try:
                return self._generate_with_provider(prompt, config, config['fallback_provider'], system_prompt)
            except Exception as e2:
                # If both providers fail, log the error and raise
                logger.error(f"Error with fallback provider {config['fallback_provider']}: {str(e2)}")
                raise Exception(f"Failed to generate content with both providers: {str(e)} | {str(e2)}")

    def _generate_with_provider(self,
                               prompt: str,
                               config: Dict[str, Any],
                               provider: str,
                               system_prompt: Optional[str] = None) -> str:
        """
        Generate content using a specific provider.

        Args:
            prompt: The prompt to send to the LLM
            config: The configuration to use
            provider: The provider to use ('openrouter' or 'requesty')
            system_prompt: Optional system prompt to use

        Returns:
            The generated content as a string
        """
        if provider == 'openrouter':
            return self._generate_with_openrouter(prompt, config, system_prompt)
        elif provider == 'requesty':
            return self._generate_with_requesty(prompt, config, system_prompt)
        else:
            raise ValueError(f"Unknown provider: {provider}")

    def _generate_with_openrouter(self,
                                 prompt: str,
                                 config: Dict[str, Any],
                                 system_prompt: Optional[str] = None) -> str:
        """
        Generate content using OpenRouter.

        Args:
            prompt: The prompt to send to the LLM
            config: The configuration to use
            system_prompt: Optional system prompt to use

        Returns:
            The generated content as a string
        """
        if not self.openrouter_api_key:
            raise ValueError("OpenRouter API key not found in environment variables")

        # Prepare the request
        url = "https://openrouter.ai/api/v1/chat/completions"

        # Prepare the messages
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add user prompt
        messages.append({"role": "user", "content": prompt})

        # Prepare the request data
        data = {
            "model": config['model'],
            "messages": messages,
            "max_tokens": config['max_tokens'],
            "temperature": config['temperature'],
            "top_p": config['top_p'],
            "frequency_penalty": config['frequency_penalty'],
            "presence_penalty": config['presence_penalty']
        }

        # Prepare the headers
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://researchassistant.uk"
        }

        # Make the request
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            # Parse the response
            result = response.json()

            # Extract the generated content
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                raise ValueError(f"Unexpected response format from OpenRouter: {result}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to OpenRouter: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def _generate_with_requesty(self,
                               prompt: str,
                               config: Dict[str, Any],
                               system_prompt: Optional[str] = None) -> str:
        """
        Generate content using Requesty.

        Args:
            prompt: The prompt to send to the LLM
            config: The configuration to use
            system_prompt: Optional system prompt to use

        Returns:
            The generated content as a string
        """
        if not self.requesty_api_key:
            raise ValueError("Requesty API key not found in environment variables")

        # Prepare the request
        url = "https://api.requesty.ai/api/v1/chat/completions"

        # Prepare the messages
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Add user prompt
        messages.append({"role": "user", "content": prompt})

        # Prepare the request data
        data = {
            "model": config['model'],
            "messages": messages,
            "max_tokens": config['max_tokens'],
            "temperature": config['temperature'],
            "top_p": config['top_p'],
            "frequency_penalty": config['frequency_penalty'],
            "presence_penalty": config['presence_penalty']
        }

        # Prepare the headers
        headers = {
            "Authorization": f"Bearer {self.requesty_api_key}",
            "Content-Type": "application/json"
        }

        # Make the request
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()

            # Parse the response
            result = response.json()

            # Extract the generated content
            if 'choices' in result and len(result['choices']) > 0:
                return result['choices'][0]['message']['content']
            else:
                raise ValueError(f"Unexpected response format from Requesty: {result}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Error making request to Requesty: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status code: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text}")
            raise

    def generate_research_plan(self, topic: str, key_points: List[str]) -> Dict[str, Any]:
        """
        Generate a research plan for a given topic.

        Args:
            topic: The research topic
            key_points: Key points to include in the research

        Returns:
            A dictionary containing the research plan
        """
        # Create a prompt for the research plan
        prompt = f"""
        Create a detailed research plan for the topic: {topic}

        Key points to address:
        {' '.join([f'- {point}' for point in key_points])}

        The research plan should include:
        1. Main research questions
        2. Subtopics to explore
        3. Key sources to consult
        4. Methodology approach

        Format the response as a structured research plan.
        """

        # Create a system prompt
        system_prompt = """
        You are a research planning assistant. Your task is to create detailed research plans for academic papers.
        Your plans should be comprehensive, well-structured, and academically rigorous.
        Provide specific research questions, subtopics, and methodological approaches.
        """

        # Generate the research plan using the planning configuration
        response = self.generate_content(prompt, config_type='planning', system_prompt=system_prompt)

        # In a real implementation, we would parse the response into a structured format
        # For now, we'll return a simple dictionary with the raw response
        return {
            "topic": topic,
            "raw_plan": response,
            "research_questions": ["What are the key aspects of this topic?", "How has this field evolved?"],
            "subtopics": ["Historical context", "Current state", "Future directions"],
            "sources": ["Academic journals", "Books", "Expert interviews"],
            "methodology": "Literature review and synthesis"
        }

    def generate_paper_content(self, topic: str, research_plan: Dict[str, Any], education_level: str, research_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate the content for a research paper.

        Args:
            topic: The research topic
            research_plan: The research plan
            education_level: The education level (e.g., 'undergraduate', 'graduate')
            research_context: Optional research context with sources and citations

        Returns:
            A dictionary containing the paper content
        """
        # Create a prompt for the paper content
        prompt = f"""
        Generate a comprehensive research paper on the topic: {topic}

        Education level: {education_level}

        Research questions:
        {' '.join([f'- {q}' for q in research_plan['research_questions']])}

        Subtopics to cover:
        {' '.join([f'- {s}' for s in research_plan['subtopics']])}

        The paper should include:
        1. Introduction
        2. Literature Review
        3. Methodology
        4. Findings/Analysis
        5. Discussion
        6. Conclusion
        7. References

        Format the response as a structured academic paper.
        """

        # Add research context if available
        if research_context:
            prompt += f"""

            Use the following sources in your paper:

            Sources:
            {' '.join([f'- {s.get("title", "Unknown")}, {s.get("publication_year", "Unknown")}' for s in research_context.get('sources', [])[:5]])}

            Citations:
            {' '.join([f'- {c}' for c in research_context.get('citations', [])[:5]])}
            """

        # Create a system prompt
        system_prompt = f"""
        You are an academic writing assistant specializing in {education_level} level research papers.
        Your task is to generate well-structured, academically rigorous research papers.
        Include proper citations, academic language, and appropriate depth for the {education_level} level.
        """

        # Generate the paper content using the content configuration
        response = self.generate_content(prompt, config_type='content', system_prompt=system_prompt)

        # In a real implementation, we would parse the response into a structured format
        # For now, we'll return a simple dictionary with the raw response
        return {
            "title": f"Research on {topic}",
            "raw_content": response,
            "abstract": f"This paper explores {topic} at the {education_level} level...",
            "introduction": f"Introduction to {topic}...",
            "literature_review": "Review of relevant literature...",
            "methodology": "Methodology used in this research...",
            "findings": "Key findings from the research...",
            "discussion": "Discussion of the implications...",
            "conclusion": "Conclusion summarizing the research...",
            "references": ["Reference 1", "Reference 2", "Reference 3"]
        }

    def analyze_paper_content(self, paper_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze the content of a paper to generate a review.

        Args:
            paper_content: Dictionary containing the paper content

        Returns:
            Dictionary containing the analysis results
        """
        # Extract the title and sections from the paper content
        title = paper_content.get("title", "Untitled Paper")
        sections = paper_content.get("sections", {})

        # Create a prompt for the paper analysis
        section_text = ""
        for section_name, section_content in sections.items():
            section_text += f"\n\n{section_name.upper()}:\n{section_content[:500]}..."

        prompt = f"""
        Analyze the following academic paper:

        TITLE: {title}

        CONTENT EXCERPTS:
        {section_text}

        Provide a comprehensive analysis including:
        1. Summary of the paper's main points and contributions
        2. Strengths of the paper
        3. Weaknesses and areas for improvement
        4. Evaluation of methodology and research approach
        5. Assessment of the paper's organization and clarity
        6. Recommendations for improvement

        Format your response as a structured analysis with clear sections.
        """

        # Create a system prompt
        system_prompt = """
        You are an academic paper reviewer with expertise across multiple disciplines.
        Your task is to provide thorough, constructive, and fair reviews of academic papers.
        Focus on both strengths and weaknesses, and provide specific recommendations for improvement.
        Your analysis should be detailed, insightful, and helpful for the author.
        """

        # Generate the analysis using the content configuration
        response = self.generate_content(prompt, config_type='content', system_prompt=system_prompt)

        # In a real implementation, we would parse the response into a structured format
        # For now, we'll create a simple structured response
        return {
            "summary": "This paper presents research on...",
            "strengths": "The paper demonstrates strong methodology and...",
            "weaknesses": "Areas for improvement include...",
            "methodology_assessment": "The methodology is appropriate but could be enhanced by...",
            "organization_assessment": "The paper is well-organized with clear sections...",
            "recommendations": "To improve this paper, the author should consider..."
        }

    def generate_review_comments(self, paper_content: Dict[str, Any], paper_analysis: Dict[str, Any]) -> str:
        """
        Generate detailed review comments for a paper based on analysis.

        Args:
            paper_content: Dictionary containing the paper content
            paper_analysis: Dictionary containing the paper analysis

        Returns:
            String containing detailed review comments
        """
        # Extract the title and sections from the paper content
        title = paper_content.get("title", "Untitled Paper")

        # Extract analysis components
        summary = paper_analysis.get("summary", "")
        strengths = paper_analysis.get("strengths", "")
        weaknesses = paper_analysis.get("weaknesses", "")
        recommendations = paper_analysis.get("recommendations", "")

        # Create a prompt for the review comments
        prompt = f"""
        Generate detailed review comments for the following academic paper:

        TITLE: {title}

        ANALYSIS SUMMARY:
        {summary}

        STRENGTHS:
        {strengths}

        WEAKNESSES:
        {weaknesses}

        RECOMMENDATIONS:
        {recommendations}

        Provide specific, actionable comments for each section of the paper, including:
        1. Line-by-line feedback on clarity, organization, and argumentation
        2. Suggestions for improving the methodology
        3. Recommendations for strengthening the literature review
        4. Comments on the quality of analysis and interpretation
        5. Suggestions for enhancing the discussion and conclusion

        Format your response as detailed review comments that would be helpful to the author.
        """

        # Create a system prompt
        system_prompt = """
        You are an academic paper reviewer providing detailed feedback to help authors improve their work.
        Your comments should be specific, constructive, and actionable.
        Balance criticism with recognition of strengths, and provide clear examples and suggestions.
        Your goal is to help the author produce the best possible version of their paper.
        """

        # Generate the review comments using the content configuration
        return self.generate_content(prompt, config_type='content', system_prompt=system_prompt)


# Create a singleton instance of the LLM service
llm_service = LLMService()
