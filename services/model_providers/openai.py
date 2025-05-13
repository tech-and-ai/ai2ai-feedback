"""
OpenAI Provider

This module provides integration with OpenAI for model inference.
"""

import logging
import json
import aiohttp
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

class OpenAIProvider:
    """OpenAI provider class."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the OpenAI provider.
        
        Args:
            config: Provider configuration
        """
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'https://api.openai.com/v1')
        self.timeout = config.get('timeout', 60)
        self.supported_models = config.get('supported_models', [])
        
        if not self.api_key:
            logger.warning("OpenAI API key not provided")
        
        logger.info(f"Initialized OpenAI provider with base URL: {self.base_url}")
    
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
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "frequency_penalty": frequency_penalty,
            "presence_penalty": presence_penalty
        }
        
        if stop_sequences:
            payload["stop"] = stop_sequences
        
        logger.info(f"Generating text with model {model}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error generating text: {error_text}")
                        raise Exception(f"Error generating text: {error_text}")
                    
                    result = await response.json()
                    return result['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """
        List available models.
        
        Returns:
            List of available models
        """
        url = f"{self.base_url}/models"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=self.timeout) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Error listing models: {error_text}")
                        raise Exception(f"Error listing models: {error_text}")
                    
                    result = await response.json()
                    return result.get('data', [])
        except Exception as e:
            logger.error(f"Error listing models: {e}")
            raise
