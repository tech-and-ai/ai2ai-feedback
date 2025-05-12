"""
Base service class for all services.

This module provides a base class for all services to inherit from,
ensuring consistent initialization and configuration.
"""
from typing import Dict, Any, Optional, Type, TypeVar
from abc import ABC, abstractmethod

from app.config import config
from app.logging import get_logger

# Get logger
logger = get_logger(__name__)

# Type variable for service class
T = TypeVar('T', bound='BaseService')

class BaseService(ABC):
    """Base class for all services."""
    
    # Class variable to store singleton instances
    _instances: Dict[Type[T], T] = {}
    
    def __init__(self):
        """Initialize the base service."""
        self.config = config
        self.logger = get_logger(self.__class__.__module__)
        self.logger.info(f"Initializing {self.__class__.__name__}")
    
    @classmethod
    def get_instance(cls: Type[T]) -> T:
        """
        Get the singleton instance of the service.
        
        Returns:
            Service instance
        """
        if cls not in cls._instances:
            cls._instances[cls] = cls()
        
        return cls._instances[cls]
    
    @classmethod
    def reset_instance(cls: Type[T]) -> None:
        """
        Reset the singleton instance of the service.
        
        This is useful for testing.
        """
        if cls in cls._instances:
            del cls._instances[cls]


class DatabaseService(BaseService):
    """Base class for services that interact with a database."""
    
    def __init__(self):
        """Initialize the database service."""
        super().__init__()
        self.db_config = {
            "url": self.config.SUPABASE_URL,
            "key": self.config.SUPABASE_KEY,
        }
        self.logger.info("Database configuration loaded")
    
    @abstractmethod
    def get_connection(self):
        """
        Get a database connection.
        
        Returns:
            Database connection
        """
        pass


class ApiService(BaseService):
    """Base class for services that interact with external APIs."""
    
    def __init__(self):
        """Initialize the API service."""
        super().__init__()
        self.api_config = {}
        self.logger.info("API configuration loaded")
    
    @abstractmethod
    def get_client(self):
        """
        Get an API client.
        
        Returns:
            API client
        """
        pass


class CacheService(BaseService):
    """Base class for services that provide caching functionality."""
    
    def __init__(self):
        """Initialize the cache service."""
        super().__init__()
        self.cache_config = {
            "ttl": self.config.CACHE_TTL if hasattr(self.config, "CACHE_TTL") else 3600,
        }
        self.logger.info(f"Cache configuration loaded with TTL: {self.cache_config['ttl']} seconds")
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Get a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if found, None otherwise
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set a value in the cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Delete a value from the cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        pass
