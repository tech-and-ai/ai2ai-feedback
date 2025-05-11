"""
OpenAI provider for AI-to-AI Feedback API
"""

import os
import httpx
from .base import ModelProvider

class OpenAIProvider(ModelProvider):
    """OpenAI model provider"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize OpenAI provider
        
        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: Model name (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("DEFAULT_MODEL", "gpt-4-turbo")
        
        # Remove provider prefix if present (e.g., "openai/gpt-4-turbo" -> "gpt-4-turbo")
        if "/" in self.model:
            self.model = self.model.split("/")[-1]
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            str: Provider name
        """
        return "openai"
    
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
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,  # Lower temperature for more focused feedback
                        "max_tokens": 4000
                    }
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                if not response_data.get("choices") or len(response_data["choices"]) == 0:
                    raise ValueError("No choices returned from OpenAI API")
                
                return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error generating completion with OpenAI: {e}")
            raise
