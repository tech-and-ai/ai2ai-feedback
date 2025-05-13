"""
Logging Utilities

This module provides utilities for setting up logging.
"""

import logging
import sys
from typing import Optional

def setup_logging(log_level: Optional[str] = None, debug: bool = False):
    """
    Set up logging.
    
    Args:
        log_level: Log level
        debug: Enable debug mode
    """
    if debug:
        log_level = "DEBUG"
    elif not log_level:
        log_level = "INFO"
    
    # Convert log level string to logging level
    numeric_level = getattr(logging, log_level.upper(), None)
    
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {log_level}")
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set log level for specific loggers
    logging.getLogger("uvicorn").setLevel(numeric_level)
    logging.getLogger("fastapi").setLevel(numeric_level)
    
    # Log configuration
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")
    
    if debug:
        logger.info("Debug mode enabled")
