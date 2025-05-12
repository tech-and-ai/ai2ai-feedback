"""
OpenRouter provider for AI-to-AI Feedback API
"""

import os
import json
import httpx
import asyncio
from typing import AsyncGenerator
from .base import ModelProvider

class OpenRouterProvider(ModelProvider):
    """OpenRouter model provider"""

    def __init__(self, api_key: str = None, model: str = None):
        """
        Initialize OpenRouter provider

        Args:
            api_key: OpenRouter API key (defaults to environment variable)
            model: Model name (defaults to environment variable)
        """
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY", "")
        self.model = model or os.getenv("DEFAULT_MODEL", "deepseek-coder-v2:16b")

        if not self.api_key:
            raise ValueError("OpenRouter API key is required")

    def get_provider_name(self) -> str:
        """
        Get the provider name

        Returns:
            str: Provider name
        """
        return "openrouter"

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
                    "http://192.168.0.77:111434/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/tech-and-ai/ai2ai-feedback",
                        "X-Title": "AI2AI Feedback API"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3  # Lower temperature for more focused feedback
                    }
                )

                response.raise_for_status()
                response_data = response.json()

                if not response_data.get("choices") or len(response_data["choices"]) == 0:
                    raise ValueError("No choices returned from OpenRouter API")

                return response_data["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"Error generating completion with OpenRouter: {e}")
            raise

    async def generate_completion_stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming completion from the model

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Yields:
            str: Generated text chunks
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    "http://192.168.0.77:111434/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://github.com/tech-and-ai/ai2ai-feedback",
                        "X-Title": "AI2AI Feedback API"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,  # Lower temperature for more focused feedback
                        "stream": True  # Enable streaming
                    },
                    timeout=120.0
                ) as response:
                    response.raise_for_status()

                    # Process the streaming response
                    async for line in response.aiter_lines():
                        # Skip empty lines and "data: [DONE]" messages
                        if not line or line == "data: [DONE]":
                            continue

                        # Remove "data: " prefix if present
                        if line.startswith("data: "):
                            line = line[6:]

                        try:
                            # Parse the JSON data
                            data = json.loads(line)

                            # Extract the content delta
                            if (
                                data.get("choices")
                                and len(data["choices"]) > 0
                                and data["choices"][0].get("delta")
                                and data["choices"][0]["delta"].get("content")
                            ):
                                content = data["choices"][0]["delta"]["content"]
                                yield content
                        except json.JSONDecodeError:
                            # Skip invalid JSON
                            continue
        except Exception as e:
            print(f"Error generating streaming completion with OpenRouter: {e}")
            raise
