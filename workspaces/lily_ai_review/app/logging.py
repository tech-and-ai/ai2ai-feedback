"""
Logging configuration for the application.

This module provides a centralized way to configure logging for the application.
"""
import logging
import logging.config
import os
import sys
from typing import Dict, Any, Optional

from app.config import config


def get_logging_config() -> Dict[str, Any]:
    """
    Get the logging configuration dictionary.
    
    Returns:
        Dict[str, Any]: Logging configuration dictionary
    """
    log_level = "DEBUG" if config.DEBUG else "INFO"
    
    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level,
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "level": log_level,
                "filename": "app.log",
                "mode": "a",
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": True,
            },
            "uvicorn": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "fastapi": {
                "handlers": ["console", "file"],
                "level": log_level,
                "propagate": False,
            },
            "stripe": {
                "handlers": ["console", "file"],
                "level": "WARNING",  # Stripe library is very verbose
                "propagate": False,
            },
        },
    }


def configure_logging() -> None:
    """Configure logging for the application."""
    try:
        # Try to import the JSON logger
        from pythonjsonlogger import jsonlogger
        json_logging_available = True
    except ImportError:
        json_logging_available = False
    
    # Get the logging configuration
    logging_config = get_logging_config()
    
    # If JSON logging is not available, remove the JSON formatter
    if not json_logging_available:
        if "json" in logging_config["formatters"]:
            del logging_config["formatters"]["json"]
    
    # Configure logging
    logging.config.dictConfig(logging_config)
    
    # Log the configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {logging_config['loggers']['']['level']}")
    logger.info(f"Application environment: {config.ENV}")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (defaults to the module name)
        
    Returns:
        logging.Logger: Logger instance
    """
    return logging.getLogger(name)
