"""
Validation Utilities

This module provides utilities for validating data.
"""

import logging
import json
import re
from typing import Tuple, Dict, Any

logger = logging.getLogger(__name__)

def validate_json(content: str) -> Tuple[bool, str]:
    """
    Validate JSON content.
    
    Args:
        content: JSON content
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not content:
        return False, "Empty content"
    
    try:
        json.loads(content)
        return True, "Valid JSON"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"

def validate_html(content: str) -> Tuple[bool, str]:
    """
    Validate HTML content.
    
    Args:
        content: HTML content
        
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
    
    # Check for balanced tags
    tag_pattern = re.compile(r'<([a-zA-Z][a-zA-Z0-9]*)[^>]*>|</([a-zA-Z][a-zA-Z0-9]*)>')
    tags = []
    
    for match in tag_pattern.finditer(content):
        opening_tag, closing_tag = match.groups()
        
        if opening_tag:
            # Self-closing tags
            if match.group(0).endswith('/>'):
                continue
            
            tags.append(opening_tag)
        elif closing_tag:
            if not tags or tags[-1] != closing_tag:
                return False, f"Mismatched tag: {closing_tag}"
            
            tags.pop()
    
    if tags:
        return False, f"Unclosed tags: {', '.join(tags)}"
    
    return True, "Valid HTML"

def validate_markdown(content: str) -> Tuple[bool, str]:
    """
    Validate Markdown content.
    
    Args:
        content: Markdown content
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not content:
        return False, "Empty content"
    
    return True, "Valid Markdown"

def validate_code(content: str, language: str = None) -> Tuple[bool, str]:
    """
    Validate code content.
    
    Args:
        content: Code content
        language: Programming language
        
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
    
    return True, "Valid code"

def validate_task_metadata(metadata: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate task metadata.
    
    Args:
        metadata: Task metadata
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not isinstance(metadata, dict):
        return False, "Metadata must be a dictionary"
    
    return True, "Valid metadata"

def validate_agent_capabilities(capabilities: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate agent capabilities.
    
    Args:
        capabilities: Agent capabilities
        
    Returns:
        Tuple of (is_valid, validation_message)
    """
    if not isinstance(capabilities, dict):
        return False, "Capabilities must be a dictionary"
    
    return True, "Valid capabilities"
