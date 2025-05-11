"""
Base provider interface for AI-to-AI Feedback API
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator

class ModelProvider(ABC):
    """Base class for model providers"""

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Get the provider name

        Returns:
            str: Provider name
        """
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """
        Get the model name

        Returns:
            str: Model name
        """
        pass

    @abstractmethod
    async def generate_completion(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a completion from the model

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            str: Generated text
        """
        pass

    @abstractmethod
    async def generate_completion_stream(self, system_prompt: str, user_prompt: str) -> AsyncGenerator[str, None]:
        """
        Generate a streaming completion from the model

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Yields:
            str: Generated text chunks
        """
        pass
