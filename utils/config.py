"""
Configuration Utilities

This module provides utilities for loading and managing configuration.
"""

import os
import logging
import importlib
from typing import Any

logger = logging.getLogger(__name__)

class Config:
    """Configuration class."""

    def __init__(self):
        """Initialize the configuration."""
        # Default configuration
        self.host = "0.0.0.0"
        self.port = 8000
        self.database_url = "ai2ai_feedback.db"
        self.log_level = "info"
        self.model_providers = {}
        self.prompt_templates = {}
        self.research = {}
        self.execution = {}

    def update(self, config_dict):
        """
        Update configuration from a dictionary.

        Args:
            config_dict: Configuration dictionary
        """
        for key, value in config_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.warning(f"Unknown configuration key: {key}")

def load_config(config_name: str) -> Config:
    """
    Load configuration.

    Args:
        config_name: Configuration name

    Returns:
        Configuration
    """
    config = Config()

    # Try to load configuration module
    try:
        config_module = importlib.import_module(f"config.{config_name}")
        config.update(config_module.CONFIG)
    except ImportError:
        logger.warning(f"Configuration module not found: {config_name}")
    except AttributeError:
        logger.warning(f"CONFIG not found in module: {config_name}")

    # Override with environment variables
    for key in dir(config):
        if key.startswith("_"):
            continue

        env_key = f"AI2AI_{key.upper()}"
        env_value = os.environ.get(env_key)

        if env_value is not None:
            # Convert environment variable to appropriate type
            current_value = getattr(config, key)

            if isinstance(current_value, bool):
                setattr(config, key, env_value.lower() in ("true", "1", "yes"))
            elif isinstance(current_value, int):
                setattr(config, key, int(env_value))
            elif isinstance(current_value, float):
                setattr(config, key, float(env_value))
            else:
                setattr(config, key, env_value)

    return config
