"""
Dependency injection container for the application.

This module provides a centralized way to manage service dependencies
and ensure proper initialization and configuration.
"""
from typing import Dict, Any, Type, TypeVar, Callable, Optional
import inspect

from app.logging import get_logger

# Get logger
logger = get_logger(__name__)

# Type variable for service class
T = TypeVar('T')

class DependencyContainer:
    """Container for managing service dependencies."""
    
    def __init__(self):
        """Initialize the dependency container."""
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable[[], Any]] = {}
        logger.info("Initializing dependency container")
    
    def register(self, service_type: Type[T], instance: T) -> None:
        """
        Register a service instance.
        
        Args:
            service_type: The type of the service
            instance: The service instance
        """
        self._services[service_type] = instance
        logger.info(f"Registered service: {service_type.__name__}")
    
    def register_factory(self, service_type: Type[T], factory: Callable[[], T]) -> None:
        """
        Register a factory function for a service.
        
        Args:
            service_type: The type of the service
            factory: Factory function that creates the service
        """
        self._factories[service_type] = factory
        logger.info(f"Registered factory for service: {service_type.__name__}")
    
    def get(self, service_type: Type[T]) -> T:
        """
        Get a service instance.
        
        Args:
            service_type: The type of the service
            
        Returns:
            Service instance
            
        Raises:
            KeyError: If the service is not registered
        """
        # Check if service is already instantiated
        if service_type in self._services:
            return self._services[service_type]
        
        # Check if there's a factory for this service
        if service_type in self._factories:
            # Create the service using the factory
            instance = self._factories[service_type]()
            # Cache the instance
            self._services[service_type] = instance
            logger.info(f"Created service using factory: {service_type.__name__}")
            return instance
        
        # Try to create the service using auto-injection
        try:
            instance = self._auto_inject(service_type)
            if instance:
                self._services[service_type] = instance
                logger.info(f"Auto-injected service: {service_type.__name__}")
                return instance
        except Exception as e:
            logger.error(f"Error auto-injecting service {service_type.__name__}: {str(e)}")
        
        # Service not found
        raise KeyError(f"Service not registered: {service_type.__name__}")
    
    def _auto_inject(self, service_type: Type[T]) -> Optional[T]:
        """
        Attempt to auto-inject dependencies for a service.
        
        Args:
            service_type: The type of the service
            
        Returns:
            Service instance if successful, None otherwise
        """
        # Get the constructor signature
        try:
            signature = inspect.signature(service_type.__init__)
            
            # Skip if the constructor has no parameters (other than self)
            if len(signature.parameters) <= 1:
                return service_type()
            
            # Collect dependencies
            args = []
            kwargs = {}
            
            for param_name, param in list(signature.parameters.items())[1:]:  # Skip 'self'
                # Get the parameter type
                param_type = param.annotation
                
                # Skip if no type annotation
                if param_type is inspect.Parameter.empty:
                    if param.default is inspect.Parameter.empty:
                        # Required parameter with no type annotation, can't auto-inject
                        return None
                    continue
                
                # Try to get the dependency
                try:
                    dependency = self.get(param_type)
                    kwargs[param_name] = dependency
                except KeyError:
                    # Dependency not found
                    if param.default is inspect.Parameter.empty:
                        # Required dependency, can't auto-inject
                        return None
            
            # Create the service with the dependencies
            return service_type(**kwargs)
            
        except Exception as e:
            logger.error(f"Error in auto-injection for {service_type.__name__}: {str(e)}")
            return None

# Singleton instance
_container = None

def get_container() -> DependencyContainer:
    """
    Get the dependency container instance.
    
    Returns:
        Dependency container instance
    """
    global _container
    
    if _container is None:
        _container = DependencyContainer()
    
    return _container
