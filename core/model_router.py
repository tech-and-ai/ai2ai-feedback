"""
Model Router

This module is responsible for routing requests to appropriate models
based on task requirements and agent assignments.
"""

import logging
import random
from typing import Dict, List, Optional, Any

from models.agent import Agent

logger = logging.getLogger(__name__)

class ModelRouter:
    """
    Model Router class for routing requests to appropriate models.
    """

    def __init__(self, model_providers_config: Dict[str, Any]):
        """
        Initialize the Model Router.

        Args:
            model_providers_config: Configuration for model providers
        """
        self.model_providers_config = model_providers_config
        self.model_providers = {}
        self._initialize_model_providers()
        logger.info("Model Router initialized")

    def _initialize_model_providers(self):
        """
        Initialize model providers based on configuration.
        """
        for provider_name, provider_config in self.model_providers_config.items():
            provider_type = provider_config.get('type')

            if provider_type == 'ollama':
                from services.model_providers.ollama import OllamaProvider
                self.model_providers[provider_name] = OllamaProvider(provider_config)
            elif provider_type == 'openai':
                from services.model_providers.openai import OpenAIProvider
                self.model_providers[provider_name] = OpenAIProvider(provider_config)
            else:
                logger.warning(f"Unknown model provider type: {provider_type}")

    async def route_request(self,
                           prompt: str,
                           agent: Agent,
                           system_prompt: Optional[str] = None,
                           max_tokens: int = 1000,
                           temperature: float = 0.7,
                           top_p: float = 1.0,
                           frequency_penalty: float = 0.0,
                           presence_penalty: float = 0.0,
                           stop_sequences: Optional[List[str]] = None) -> str:
        """
        Route a request to the appropriate model based on agent configuration.

        Args:
            prompt: Prompt to send to the model
            agent: Agent making the request
            system_prompt: Optional system prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p for nucleus sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop_sequences: Optional stop sequences

        Returns:
            Model response
        """
        model = agent.model
        provider_name = self._get_provider_for_model(model)

        if not provider_name:
            logger.error(f"No provider found for model: {model}")
            raise ValueError(f"No provider found for model: {model}")

        provider = self.model_providers[provider_name]

        logger.info(f"Routing request to model {model} via provider {provider_name}")

        try:
            response = await provider.generate(
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop_sequences=stop_sequences
            )

            return response
        except Exception as e:
            logger.error(f"Error generating response from model {model}: {e}")

            # Try fallback if available
            fallback_response = await self._try_fallback(
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                frequency_penalty=frequency_penalty,
                presence_penalty=presence_penalty,
                stop_sequences=stop_sequences
            )

            if fallback_response:
                return fallback_response

            raise

    def _get_provider_for_model(self, model: str) -> Optional[str]:
        """
        Get the provider for a model.

        Args:
            model: Model identifier

        Returns:
            Provider name if found, None otherwise
        """
        # First check for exact model support
        for provider_name, provider in self.model_providers.items():
            if provider.supports_model(model):
                return provider_name

        # If no exact match, use the first provider as default
        if self.model_providers:
            return next(iter(self.model_providers))

        return None

    async def _try_fallback(self,
                           model: str,
                           prompt: str,
                           system_prompt: Optional[str] = None,
                           max_tokens: int = 1000,
                           temperature: float = 0.7,
                           top_p: float = 1.0,
                           frequency_penalty: float = 0.0,
                           presence_penalty: float = 0.0,
                           stop_sequences: Optional[List[str]] = None) -> Optional[str]:
        """
        Try to use a fallback model if the primary model fails.

        Args:
            model: Primary model identifier
            prompt: Prompt to send to the model
            system_prompt: Optional system prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            top_p: Top-p for nucleus sampling
            frequency_penalty: Frequency penalty
            presence_penalty: Presence penalty
            stop_sequences: Optional stop sequences

        Returns:
            Fallback model response if successful, None otherwise
        """
        # Get fallback models for the primary model
        fallback_models = self._get_fallback_models(model)

        if not fallback_models:
            logger.warning(f"No fallback models available for {model}")
            return None

        # Try each fallback model
        for fallback_model in fallback_models:
            provider_name = self._get_provider_for_model(fallback_model)

            if not provider_name:
                logger.warning(f"No provider found for fallback model: {fallback_model}")
                continue

            provider = self.model_providers[provider_name]

            logger.info(f"Trying fallback model {fallback_model} via provider {provider_name}")

            try:
                response = await provider.generate(
                    model=fallback_model,
                    prompt=prompt,
                    system_prompt=system_prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    frequency_penalty=frequency_penalty,
                    presence_penalty=presence_penalty,
                    stop_sequences=stop_sequences
                )

                return response
            except Exception as e:
                logger.error(f"Error generating response from fallback model {fallback_model}: {e}")

        return None

    def _get_fallback_models(self, model: str) -> List[str]:
        """
        Get fallback models for a primary model.

        Args:
            model: Primary model identifier

        Returns:
            List of fallback model identifiers
        """
        # Define fallback models for each primary model
        fallbacks = {
            'gemma3:4b': ['gemma3:1b'],
            'deepseek-coder-v2:16b': ['gemma3:4b', 'gemma3:1b'],
            'llama3:8b': ['gemma3:4b', 'gemma3:1b'],
        }

        return fallbacks.get(model, [])
