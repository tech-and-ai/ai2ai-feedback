"""
Anthropic provider for AI-to-AI Feedback API
"""

import os
import httpx
from .base import ModelProvider

class AnthropicProvider(ModelProvider):
    """Anthropic model provider"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Anthropic provider
        
        Args:
            api_key: Anthropic API key (defaults to environment variable)
            model: Model name (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("DEFAULT_MODEL", "claude-3-opus-20240229")
        
        # Remove provider prefix if present (e.g., "anthropic/claude-3-opus-20240229" -> "claude-3-opus-20240229")
        if "/" in self.model:
            self.model = self.model.split("/")[-1]
        
        if not self.api_key:
            raise ValueError("Anthropic API key is required")
    
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            str: Provider name
        """
        return "anthropic"
    
    def get_model_name(self) -> str:
        """
        Get the model name
        
        Returns:
            str: Model name
        """
        return self.model
    
    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a completion from the model
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            
        Returns:
            str: Generated text
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "system": system_prompt,
                        "messages": [
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,  # Lower temperature for more focused feedback
                        "max_tokens": 4000
                    }
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                if not response_data.get("content") or len(response_data["content"]) == 0:
                    raise ValueError("No content returned from Anthropic API")
                
                return response_data["content"][0]["text"]
        except Exception as e:
            print(f"Error generating completion with Anthropic: {e}")
            raise
