"""
Google provider for AI-to-AI Feedback API
"""

import os
import httpx
from typing import List, Dict, Any
from .base import ModelProvider

class GoogleProvider(ModelProvider):
    """Google model provider"""
    
    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize Google provider
        
        Args:
            api_key: Google API key (defaults to environment variable)
            model: Model name (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model or os.getenv("DEFAULT_MODEL", "gemini-pro")
        
        # Remove provider prefix if present (e.g., "google/gemini-pro" -> "gemini-pro")
        if self.model.startswith("google/"):
            self.model = self.model[len("google/"):]
    
    def get_provider_name(self) -> str:
        """
        Get the provider name
        
        Returns:
            str: Provider name
        """
        return "google"
    
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
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                    headers={
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key
                    },
                    json={
                        "contents": messages,
                        "generationConfig": {
                            "temperature": 0.3,
                            "topP": 0.8,
                            "topK": 40,
                            "maxOutputTokens": 8192
                        }
                    }
                )
                
                response.raise_for_status()
                response_data = response.json()
                
                if not response_data.get("candidates") or not response_data["candidates"][0].get("content"):
                    raise ValueError("No response returned from Google API")
                
                return response_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Error generating completion with Google: {e}")
            raise
    
    async def list_models(self) -> List[str]:
        """
        List available models from Google
        
        Returns:
            List[str]: List of available models
        """
        # Google doesn't have a simple API to list models, so we return a hardcoded list
        return ["gemini-pro", "gemini-pro-vision", "gemini-ultra"]
