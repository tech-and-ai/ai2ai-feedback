"""
Ollama Provider

This module provides integration with Ollama for model inference.
"""

import logging
import json
import aiohttp
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class OllamaProvider:
    """Ollama provider class."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Ollama provider.
        
        Args:
            config: Provider configuration
        """
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.timeout = config.get('timeout', 60)
        self.supported_models = config.get('supported_models', [])
        logger.info(f"Initialized Ollama provider with base URL: {self.base_url}")
    
    def supports_model(self, model: str) -> bool:
        """
        Check if the provider supports a model.
        
        Args:
            model: Model identifier
            
        Returns:
            True if the model is supported, False otherwise
        """
        if not self.supported_models:
            # If no supported models are specified, assume all models are supported
            return True
        
        return model in self.supported_models
    
    async def generate(self,
                      model: str,
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      max_tokens: int = 1000,
                      temperature: float = 0.7,
                      top_p: float = 1.0,
                      frequency_penalty: float = 0.0,
                      presence_penalty: float = 0.0,
                      stop_sequences: Optional[List[str]] = None) -> str:
        """
        Generate text using the model.
        
        Args:
            model: Model identifier
            prompt: Prompt to send to the model
            system_prompt: Optional system prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p for nucleus sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop_sequences: Optional stop sequences
            
        Returns:
            Generated text
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": max_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "frequency_penalty": frequency_penalty,
                "presence_penalty": presence_penalty
            }
        }
        
        if system_prompt:
            payload["system"] = system_prompt
        
        if stop_sequences:
            payload["options"]["stop"] = stop_sequences
        
        logger.info(f"Generating text with model {model}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error generating text: {error_text}")
                        raise Exception(f"Error generating text: {error_text}")
                    
                    result = await response.json()
                    return result.get('response', '')
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of available models
        """
        url = f"{self.base_url}/api/tags"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error listing models: {error_text}")
                        raise Exception(f"Error listing models: {error_text}")
                    
                    result = await response.json()
                    return result.get('models', [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise
