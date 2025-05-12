"""
Content Generator for Diagram Orchestrator

Handles the generation of content for diagrams using LLMs.
"""
import os
import re
import sys
import logging
import aiohttp
import json
from typing import Dict, Any, Optional
from pathlib import Path
import dotenv

# Set up logging
logger = logging.getLogger(__name__)

class ContentGenerator:
    """Handles generation of content for diagrams using LLMs."""

    def __init__(self, openrouter_key: Optional[str] = None, requesty_key: Optional[str] = None):
        """
        Initialize the content generator.

        Args:
            openrouter_key: Optional API key for OpenRouter
            requesty_key: Optional API key for Requesty (fallback)
        """
        # Load environment variables from the app/.env file
        env_path = Path("/home/admin/projects/kdd/app/.env")
        if env_path.exists():
            dotenv.load_dotenv(dotenv_path=env_path)
            logger.info(f"Loaded environment variables from {env_path}")
        else:
            logger.warning(f"Environment file not found at {env_path}")

        # Get the OpenRouter API key
        self.openrouter_key = openrouter_key or os.getenv("OPENROUTER_API_KEY")
        if not self.openrouter_key:
            logger.error("OpenRouter API key not found in environment variables")
        else:
            logger.info("OpenRouter API key loaded successfully")

        # Get the Requesty API key (fallback)
        self.requesty_key = requesty_key or os.getenv("REQUESTY_API_KEY")
        if not self.requesty_key:
            logger.warning("Requesty API key not found in environment variables (fallback unavailable)")
        else:
            logger.info("Requesty API key loaded successfully (fallback available)")

        # Get API endpoints from the database
        try:
            from app.services.config.config_service import config_service
            self.openrouter_endpoint = config_service.get_config('openrouter_endpoint', 'https://openrouter.ai/api/v1/chat/completions')
            self.requesty_endpoint = config_service.get_config('requesty_endpoint', 'https://router.requesty.ai/v1/chat/completions')
            logger.info(f"Using OpenRouter endpoint from config: {self.openrouter_endpoint}")
            logger.info(f"Using Requesty endpoint from config: {self.requesty_endpoint}")
        except Exception as e:
            logger.warning(f"Error getting API endpoints from config: {str(e)}")
            # Fallback to default endpoints
            self.openrouter_endpoint = "https://openrouter.ai/api/v1/chat/completions"
            self.requesty_endpoint = "https://router.requesty.ai/v1/chat/completions"
            logger.info(f"Using default OpenRouter endpoint: {self.openrouter_endpoint}")
            logger.info(f"Using default Requesty endpoint: {self.requesty_endpoint}")

        # Default model
        try:
            # Try to import the config service
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
            from app.services.config.config_service import config_service
            self.model = config_service.get_config('default_llm_model', 'google/gemini-2.5-flash-preview')
            logger.info(f"Using model from config: {self.model}")
        except Exception as e:
            logger.warning(f"Could not load model from config service: {str(e)}")
            self.model = "google/gemini-2.5-flash-preview"  # Fallback model
            logger.info(f"Using fallback model: {self.model}")

        # Patterns for detecting provider rejections
        self.rejection_patterns = [
            r"I('m| am) (unable|not able) to (assist|help|provide|generate|create)",
            r"I cannot (provide|assist|help|generate|create)",
            r"I don't have (information|details|data|knowledge) (on|about)",
            r"This (content|request|topic) may violate",
            r"I apologize, but I (cannot|can't|am unable to)",
            r"That's not something I can (help|assist) with",
            r"I'm not (programmed|designed|built|made) to provide",
            r"(content policy|terms of service|content guidelines)",
            r"I can't (generate|create|provide) content (about|related to|on)",
            r"(harmful|illegal|unethical|inappropriate) (content|activities|topics)"
        ]

        # Compile the patterns for efficiency
        self.compiled_rejection_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.rejection_patterns]

    def _detect_provider_rejection(self, content: str) -> bool:
        """Detect if the content appears to be a provider rejection."""
        # Check if content is unusually short (potential sign of rejection)
        if len(content.strip()) < 50:
            logger.warning(f"Content suspiciously short ({len(content.strip())} chars), may be a rejection")
            return True

        # Check for common rejection patterns
        for pattern in self.compiled_rejection_patterns:
            if pattern.search(content):
                logger.warning(f"Detected potential provider rejection: {pattern.pattern}")
                return True

        # Check for non-responsiveness (doesn't address the topic)
        if "I cannot" in content and "provide" in content and "information" in content:
            logger.warning("Detected generic refusal response")
            return True

        return False

    async def generate_content(self, prompt: str, max_tokens: int = 2000, output_format: str = None) -> str:
        """
        Generate content using the provided prompt.

        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum number of tokens to generate
            output_format: Optional format specification (e.g., "json")

        Returns:
            The generated content

        Raises:
            ValueError: If both OpenRouter and Requesty APIs fail
        """
        logger.info(f"CONTENT GENERATOR DEBUG: generate_content called with prompt: {prompt[:100]}...")
        logger.info(f"CONTENT GENERATOR DEBUG: OpenRouter key available: {bool(self.openrouter_key)}")
        logger.info(f"CONTENT GENERATOR DEBUG: Requesty key available: {bool(self.requesty_key)}")

        # Check if we have at least one API key
        if not self.openrouter_key and not self.requesty_key:
            error_msg = "Cannot generate content: No API keys available"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Try OpenRouter first
        if self.openrouter_key:
            try:
                # Generate content with OpenRouter
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are an expert academic writer and researcher. You only provide content for legitimate academic purposes. You maintain academic integrity and ethical standards in all responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": max_tokens,
                    "provider": {
                        "allow_fallbacks": True
                    }
                }

                headers = {
                    "Authorization": f"Bearer {self.openrouter_key}",
                    "Content-Type": "application/json"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(self.openrouter_endpoint, headers=headers, json=payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Error from OpenRouter API: Status {response.status}, Response: {error_text}")
                            # Don't return here, fall through to Requesty
                        else:
                            data = await response.json()

                            if "choices" in data and data["choices"] and "message" in data["choices"][0] and "content" in data["choices"][0]["message"]:
                                content = data["choices"][0]["message"]["content"].strip()

                                # Check for provider rejections
                                if not self._detect_provider_rejection(content):
                                    logger.info(f"Generated content with OpenRouter: {content[:100]}...")

                                    # If JSON format is requested, try to parse and format the response
                                    if output_format == "json":
                                        try:
                                            # Try to extract JSON from the response
                                            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                                            if json_match:
                                                content = json_match.group(1).strip()

                                            # Validate that it's proper JSON
                                            json.loads(content)
                                        except (json.JSONDecodeError, ValueError) as e:
                                            logger.warning(f"Generated content is not valid JSON: {str(e)}")
                                            # Continue to Requesty if JSON validation fails
                                        else:
                                            return content
                                    else:
                                        return content
                                else:
                                    logger.warning("Provider rejection detected from OpenRouter, trying Requesty")
            except Exception as e:
                logger.error(f"Error with OpenRouter API: {str(e)}")
                # Don't return here, fall through to Requesty

        # Try Requesty as fallback
        if self.requesty_key:
            try:
                logger.info("Falling back to Requesty API")

                # Generate content with Requesty
                requesty_payload = {
                    "model": self.model,  # Using model from config
                    "messages": [
                        {"role": "system", "content": "You are an expert academic writer and researcher. You only provide content for legitimate academic purposes. You maintain academic integrity and ethical standards in all responses."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": max_tokens
                }

                requesty_headers = {
                    "Authorization": f"Bearer {self.requesty_key}",
                    "Content-Type": "application/json"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(self.requesty_endpoint, headers=requesty_headers, json=requesty_payload) as response:
                        if response.status != 200:
                            error_text = await response.text()
                            logger.error(f"Error from Requesty API: Status {response.status}, Response: {error_text}")
                            raise ValueError("Both OpenRouter and Requesty APIs failed")

                        data = await response.json()

                        if "choices" not in data or not data["choices"] or "message" not in data["choices"][0] or "content" not in data["choices"][0]["message"]:
                            logger.error("Unexpected response format from Requesty API")
                            raise ValueError("Both OpenRouter and Requesty APIs failed with unexpected response format")

                        content = data["choices"][0]["message"]["content"].strip()

                        # Check for provider rejections
                        if self._detect_provider_rejection(content):
                            logger.warning("Provider rejection detected from Requesty API")
                            raise ValueError("Both OpenRouter and Requesty APIs rejected the content generation")

                        logger.info(f"Generated content with Requesty: {content[:100]}...")

                        # If JSON format is requested, try to parse and format the response
                        if output_format == "json":
                            try:
                                # Try to extract JSON from the response
                                json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
                                if json_match:
                                    content = json_match.group(1).strip()

                                # Validate that it's proper JSON
                                json.loads(content)
                            except (json.JSONDecodeError, ValueError) as e:
                                logger.error(f"Generated content is not valid JSON: {str(e)}")
                                raise ValueError("Failed to generate valid JSON content")

                        return content
            except Exception as e:
                logger.error(f"Error with Requesty API: {str(e)}")
                raise ValueError(f"Both OpenRouter and Requesty APIs failed: {str(e)}")
        else:
            # If we get here, OpenRouter failed and Requesty is not available
            raise ValueError("OpenRouter API failed and Requesty API is not available")
