"""
Configuration Service for the Lily AI Research Assistant.

This module provides functionality to retrieve configuration settings from the database.
It ensures that model names and other settings are never hardcoded in the code.
"""

import logging
from typing import Dict, Any, Optional, Union
import os
import functools
from functools import lru_cache

from supabase import create_client
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger(__name__)

class ConfigService:
    """
    Service for retrieving configuration settings from the database.

    This class provides methods to:
    - Retrieve configuration settings
    - Cache configuration settings for performance
    - Provide fallback values if database access fails
    """

    def __init__(self):
        """
        Initialize the configuration service.

        Loads Supabase credentials from environment variables and initializes the client.
        """
        # Load environment variables
        load_dotenv()

        # Get Supabase credentials from environment variables
        supabase_url = os.environ.get("SUPABASE_PROJECT_URL")
        supabase_key = os.environ.get("SUPABASE_API_KEY")

        if not supabase_url or not supabase_key:
            logger.error("Supabase URL or key not found in environment variables")
            self.supabase = None
            logger.warning("Using fallback configuration values")
            return

        try:
            # Initialize Supabase client
            self.supabase = create_client(supabase_url, supabase_key)
            logger.info("Configuration service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing ConfigService: {str(e)}")
            self.supabase = None
            logger.warning("Using fallback configuration values")

    @lru_cache(maxsize=128)
    def get_config(self, key: str, default: Optional[str] = None) -> str:
        """
        Get a configuration value from the database.

        Args:
            key: The configuration key to retrieve
            default: Default value to return if the key is not found

        Returns:
            The configuration value as a string
        """
        try:
            if self.supabase is None:
                logger.warning(f"Using default value for {key}: {default}")
                return default if default is not None else ""

            # Query the database for the configuration value
            result = self.supabase.table('saas_lily_ai_config') \
                .select('config_value') \
                .eq('config_key', key) \
                .eq('enabled', True) \
                .execute()

            if not result.data:
                logger.warning(f"Configuration key {key} not found, using default: {default}")
                return default if default is not None else ""

            return result.data[0]['config_value']

        except Exception as e:
            logger.error(f"Error retrieving configuration {key}: {str(e)}")
            return default if default is not None else ""

    def get_config_int(self, key: str, default: int = 0) -> int:
        """
        Get a configuration value as an integer.

        Args:
            key: The configuration key to retrieve
            default: Default value to return if the key is not found or not an integer

        Returns:
            The configuration value as an integer
        """
        value = self.get_config(key, str(default))
        try:
            return int(value)
        except (ValueError, TypeError):
            logger.error(f"Configuration {key} is not a valid integer: {value}")
            return default

    def get_config_float(self, key: str, default: float = 0.0) -> float:
        """
        Get a configuration value as a float.

        Args:
            key: The configuration key to retrieve
            default: Default value to return if the key is not found or not a float

        Returns:
            The configuration value as a float
        """
        value = self.get_config(key, str(default))
        try:
            return float(value)
        except (ValueError, TypeError):
            logger.error(f"Configuration {key} is not a valid float: {value}")
            return default

    def get_config_bool(self, key: str, default: bool = False) -> bool:
        """
        Get a configuration value as a boolean.

        Args:
            key: The configuration key to retrieve
            default: Default value to return if the key is not found or not a boolean

        Returns:
            The configuration value as a boolean
        """
        value = self.get_config(key, str(default)).lower()
        if value in ('true', 't', 'yes', 'y', '1'):
            return True
        elif value in ('false', 'f', 'no', 'n', '0'):
            return False
        else:
            logger.error(f"Configuration {key} is not a valid boolean: {value}")
            return default

    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get the LLM configuration settings.

        Returns:
            Dictionary containing LLM configuration settings
        """
        return {
            'model': self.get_config('default_llm_model', 'google/gemini-2.5-flash-preview'),
            'provider': self.get_config('primary_llm_provider', 'openrouter'),
            'fallback_provider': self.get_config('fallback_llm_provider', 'requesty'),
            'fallback_model': self.get_config('fallback_llm_model', 'google/gemini-2.5-flash-preview'),
            'max_tokens': self.get_config_int('max_tokens_default', 8000),
            'temperature': self.get_config_float('temperature_default', 0.7),
            'top_p': self.get_config_float('top_p_default', 0.9),
            'frequency_penalty': self.get_config_float('frequency_penalty_default', 0.0),
            'presence_penalty': self.get_config_float('presence_penalty_default', 0.0)
        }

    def get_content_llm_config(self) -> Dict[str, Any]:
        """
        Get the content generation LLM configuration settings.

        Returns:
            Dictionary containing content LLM configuration settings
        """
        return {
            'model': self.get_config('content_llm_model', 'google/gemini-2.5-flash-preview'),
            'provider': self.get_config('primary_llm_provider', 'openrouter'),
            'fallback_provider': self.get_config('fallback_llm_provider', 'requesty'),
            'fallback_model': self.get_config('fallback_llm_model', 'google/gemini-2.5-flash-preview'),
            'max_tokens': self.get_config_int('max_tokens_content', 16000),
            'temperature': self.get_config_float('temperature_content', 0.7),
            'top_p': self.get_config_float('top_p_default', 0.9),
            'frequency_penalty': self.get_config_float('frequency_penalty_default', 0.0),
            'presence_penalty': self.get_config_float('presence_penalty_default', 0.0)
        }

    def get_planning_llm_config(self) -> Dict[str, Any]:
        """
        Get the planning LLM configuration settings.

        Returns:
            Dictionary containing planning LLM configuration settings
        """
        return {
            'model': self.get_config('planning_llm_model', 'google/gemini-2.5-flash-preview'),
            'provider': self.get_config('primary_llm_provider', 'openrouter'),
            'fallback_provider': self.get_config('fallback_llm_provider', 'requesty'),
            'fallback_model': self.get_config('fallback_llm_model', 'google/gemini-2.5-flash-preview'),
            'max_tokens': self.get_config_int('max_tokens_planning', 8000),
            'temperature': self.get_config_float('temperature_planning', 0.5),
            'top_p': self.get_config_float('top_p_default', 0.9),
            'frequency_penalty': self.get_config_float('frequency_penalty_default', 0.0),
            'presence_penalty': self.get_config_float('presence_penalty_default', 0.0)
        }

    def get_research_llm_config(self) -> Dict[str, Any]:
        """
        Get the research LLM configuration settings.

        Returns:
            Dictionary containing research LLM configuration settings
        """
        return {
            'model': self.get_config('research_llm_model', 'google/gemini-2.5-flash-preview'),
            'provider': self.get_config('primary_llm_provider', 'openrouter'),
            'fallback_provider': self.get_config('fallback_llm_provider', 'requesty'),
            'fallback_model': self.get_config('fallback_llm_model', 'google/gemini-2.5-flash-preview'),
            'max_tokens': self.get_config_int('max_tokens_default', 8000),
            'temperature': self.get_config_float('temperature_default', 0.7),
            'top_p': self.get_config_float('top_p_default', 0.9),
            'frequency_penalty': self.get_config_float('frequency_penalty_default', 0.0),
            'presence_penalty': self.get_config_float('presence_penalty_default', 0.0)
        }

    def get_worker_config(self) -> Dict[str, Any]:
        """
        Get the worker configuration settings.

        Returns:
            Dictionary containing worker configuration settings
        """
        return {
            'max_jobs': self.get_config_int('worker_max_jobs', 1),
            'poll_interval': self.get_config_int('worker_poll_interval', 5),
            'job_timeout': self.get_config_int('worker_job_timeout', 3600),  # Default 1 hour timeout
            'retry_limit': self.get_config_int('worker_retry_limit', 3),
            'retry_delay': self.get_config_int('worker_retry_delay', 300)  # Default 5 minutes delay
        }

    @functools.lru_cache(maxsize=32)
    def get_prompt(self, usage_context: str, sub_context: str = None) -> Dict[str, Any]:
        """
        Get a prompt from the database.

        Args:
            usage_context: The context in which the prompt will be used
            sub_context: Optional sub-context for more specific prompt selection

        Returns:
            Dictionary containing the prompt data
        """
        try:
            if self.supabase is None:
                logger.warning(f"Supabase client not initialized, cannot retrieve prompt for context: {usage_context}")
                return None

            # Build the query using Supabase
            query = self.supabase.table('saas_prompts').select('*').eq('usage_context', usage_context).eq('enabled', True).eq('is_current_version', True)

            # Add sub_context if provided
            if sub_context:
                query = query.eq('sub_context', sub_context)

            # Execute the query
            result = query.execute()

            if result.data and len(result.data) > 0:
                prompt = result.data[0]
                logger.info(f"Retrieved prompt: {prompt['name']}")
                return prompt
            else:
                logger.warning(f"No prompt found for context: {usage_context}, sub_context: {sub_context}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving prompt: {str(e)}")
            return None

    @functools.lru_cache(maxsize=1)
    def get_enabled_citation_style(self) -> Dict[str, Any]:
        """
        Get the currently enabled citation style from the database.

        Returns:
            Dictionary containing the citation style data, or None if no style is enabled
        """
        try:
            if self.supabase is None:
                logger.warning("Supabase client not initialized, defaulting to Harvard citation style")
                return self._get_default_harvard_style()

            # Query using Supabase
            result = self.supabase.table('saas_citation_styles').select('*').eq('enabled', True).execute()

            if result.data and len(result.data) > 0:
                style = result.data[0]
                logger.info(f"Retrieved enabled citation style: {style['name']}")
                return style
            else:
                logger.warning("No enabled citation style found, defaulting to Harvard")
                return self._get_default_harvard_style()

        except Exception as e:
            logger.error(f"Error retrieving citation style: {str(e)}")
            return self._get_default_harvard_style()

    def _get_default_harvard_style(self) -> Dict[str, Any]:
        """
        Returns a default Harvard citation style.

        Returns:
            Dictionary containing the default Harvard citation style
        """
        return {
            "name": "Harvard",
            "description": "Harvard referencing style (British Standard)",
            "format_example": "Smith, J. (2020) Title of the Article. Journal Name, 10(2), pp. 123-145. Available at: http://example.com (Accessed: 1 January 2023).",
            "enabled": True
        }

    def refresh_cache(self):
        """
        Clear the configuration cache to force fresh retrieval from the database.
        """
        self.get_config.cache_clear()
        self.get_prompt.cache_clear()
        self.get_enabled_citation_style.cache_clear()
        logger.info("Configuration cache cleared")


# Create a singleton instance of the ConfigService
config_service = ConfigService()

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Get LLM configuration
    llm_config = config_service.get_llm_config()
    print(f"LLM Model: {llm_config['model']}")
    print(f"LLM Provider: {llm_config['provider']}")
    print(f"Fallback Provider: {llm_config['fallback_provider']}")
    print(f"Max Tokens: {llm_config['max_tokens']}")
