"""
Provider factory for AI-to-AI Feedback API
"""

import os
from typing import Dict, Optional
from .base import ModelProvider
from .openrouter import OpenRouterProvider
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .ollama import OllamaProvider
from .google import GoogleProvider

# Cache for providers
provider_cache: Dict[str, ModelProvider] = {}

def get_model_provider(provider_name: Optional[str] = None, model_name: Optional[str] = None) -> ModelProvider:
    """
    Get a model provider instance

    Args:
        provider_name: Provider name (defaults to environment variable)
        model_name: Model name (defaults to environment variable)

    Returns:
        ModelProvider: Model provider instance
    """
    # Get provider name from environment variable if not provided
    if not provider_name:
        provider_name = os.getenv("DEFAULT_PROVIDER", "ollama")

    # Check if provider is already cached
    cache_key = f"{provider_name}:{model_name or ''}"
    if cache_key in provider_cache:
        return provider_cache[cache_key]

    # Create provider instance
    provider: ModelProvider

    if provider_name == "openrouter":
        provider = OpenRouterProvider(model=model_name)
    elif provider_name == "anthropic":
        provider = AnthropicProvider(model=model_name)
    elif provider_name == "openai":
        provider = OpenAIProvider(model=model_name)
    elif provider_name == "ollama":
        provider = OllamaProvider(model=model_name)
    elif provider_name == "google" or provider_name.startswith("google/"):
        provider = GoogleProvider(model=model_name)
    else:
        raise ValueError(f"Unknown provider: {provider_name}")

    # Cache provider
    provider_cache[cache_key] = provider

    return provider
