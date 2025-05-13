"""
Ollama provider for AI-to-AI Feedback API
"""

import os
import json
import httpx
from typing import List
from .base import ModelProvider

class OllamaProvider(ModelProvider):
    """Ollama model provider"""

    def __init__(self, endpoint: str = None, model: str = None):
        """
        Initialize Ollama provider

        Args:
            endpoint: Ollama API endpoint (defaults to environment variable)
            model: Model name (defaults to environment variable)
        """
        # Use the provided endpoint if available
        if endpoint:
            # Make sure the endpoint has the http:// prefix
            if not endpoint.startswith("http://") and not endpoint.startswith("https://"):
                endpoint = f"http://{endpoint}"
            self.endpoint = endpoint
        else:
            # Default endpoint
            self.endpoint = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")

        self.model = model or os.getenv("DEFAULT_MODEL", "gemma3:1b")

        # Remove trailing slash if present
        if self.endpoint.endswith("/"):
            self.endpoint = self.endpoint[:-1]

        # Remove provider prefix if present (e.g., "ollama/llama3" -> "llama3")
        if "/" in self.model:
            self.model = self.model.split("/")[-1]

    def get_provider_name(self) -> str:
        """
        Get the provider name

        Returns:
            str: Provider name
        """
        return "ollama"

    def get_model_name(self) -> str:
        """
        Get the model name

        Returns:
            str: Model name
        """
        return self.model

    async def generate_text(self, prompt: str) -> str:
        """
        Generate text from the model with a single prompt

        Args:
            prompt: The prompt to send to the model

        Returns:
            str: Generated text
        """
        # For Ollama, we'll use the prompt as both system and user prompt
        return await self.generate_completion("You are a helpful AI assistant.", prompt)

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
            # Combine system prompt and user prompt for Ollama
            prompt = f"{system_prompt}\n\n{user_prompt}"

            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for local models
                response = await client.post(
                    f"{self.endpoint}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "temperature": 0.3,  # Lower temperature for more focused feedback
                        "stream": False
                    }
                )

                response.raise_for_status()
                response_data = response.json()

                if not response_data.get("response"):
                    raise ValueError("No response returned from Ollama API")

                return response_data["response"]
        except Exception as e:
            print(f"Error generating completion with Ollama: {e}")
            raise

    async def generate_completion_stream(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a streaming completion from the model

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            str: Generated text
        """
        try:
            # Combine system prompt and user prompt for Ollama
            prompt = f"{system_prompt}\n\n{user_prompt}"

            async with httpx.AsyncClient(timeout=120.0) as client:  # Longer timeout for local models
                response = await client.post(
                    f"{self.endpoint}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "system": system_prompt,
                        "temperature": 0.3,  # Lower temperature for more focused feedback
                        "stream": True
                    }
                )

                response.raise_for_status()

                # For non-streaming, just return the full response
                full_response = ""
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                full_response += data["response"]
                        except json.JSONDecodeError:
                            pass

                return full_response
        except Exception as e:
            print(f"Error generating streaming completion with Ollama: {e}")
            raise

    async def list_models(self) -> List[str]:
        """
        List available models from Ollama

        Returns:
            List[str]: List of available models
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.endpoint}/api/tags")

                response.raise_for_status()
                response_data = response.json()

                if not response_data.get("models"):
                    return []

                return [model["name"] for model in response_data["models"]]
        except Exception as e:
            print(f"Error listing Ollama models: {e}")
            return []
