"""
Base classes for tool definitions and registry.
"""
import inspect
import json
import logging
from typing import Any, Dict, List, Optional, Type, Callable, get_type_hints

logger = logging.getLogger(__name__)

class Tool:
    """Base class for all tools."""
    
    name: str
    description: str
    parameters_schema: Dict[str, Any]
    
    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any], func: Callable):
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema
        self._func = func
        
    def execute(self, **kwargs) -> Any:
        """Execute the tool with the provided parameters."""
        try:
            return self._func(**kwargs)
        except Exception as e:
            logger.error(f"Error executing tool {self.name}: {str(e)}")
            raise ToolExecutionError(f"Error executing {self.name}: {str(e)}")
    
    @classmethod
    def from_function(cls, func: Callable, name: Optional[str] = None, 
                     description: Optional[str] = None) -> 'Tool':
        """Create a tool from a function using type hints and docstring."""
        if name is None:
            name = func.__name__
            
        if description is None:
            description = func.__doc__ or f"Tool for {name}"
            
        # Get parameter info from type hints
        type_hints = get_type_hints(func)
        signature = inspect.signature(func)
        
        # Build parameters schema
        properties = {}
        required = []
        
        for param_name, param in signature.parameters.items():
            if param_name == 'self':  # Skip self for class methods
                continue
                
            param_type = type_hints.get(param_name, Any)
            param_schema = {"type": "string"}  # Default
            
            # Convert Python types to JSON schema types
            if param_type == int:
                param_schema = {"type": "integer"}
            elif param_type == float:
                param_schema = {"type": "number"}
            elif param_type == bool:
                param_schema = {"type": "boolean"}
            elif param_type == list or param_type == List:
                param_schema = {"type": "array"}
            elif param_type == dict or param_type == Dict:
                param_schema = {"type": "object"}
                
            # Add description from docstring if available
            if func.__doc__:
                param_doc = _extract_param_doc(func.__doc__, param_name)
                if param_doc:
                    param_schema["description"] = param_doc
                    
            properties[param_name] = param_schema
            
            # Check if parameter is required
            if param.default == inspect.Parameter.empty:
                required.append(param_name)
                
        parameters_schema = {
            "type": "object",
            "properties": properties,
            "required": required
        }
        
        return cls(name, description, parameters_schema, func)


class ToolRegistry:
    """Registry for all available tools."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ToolRegistry, cls).__new__(cls)
            cls._instance.tools = {}
        return cls._instance
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self.tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")
        
    def register_function(self, func: Callable, name: Optional[str] = None, 
                         description: Optional[str] = None) -> Tool:
        """Register a function as a tool."""
        tool = Tool.from_function(func, name, description)
        self.register_tool(tool)
        return tool
        
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
        
    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with their schemas."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema
            }
            for tool in self.tools.values()
        ]
        
    def execute_tool(self, name: str, parameters: Dict[str, Any]) -> Any:
        """Execute a tool by name with the provided parameters."""
        tool = self.get_tool(name)
        if not tool:
            raise ToolNotFoundError(f"Tool {name} not found")
        return tool.execute(**parameters)


class ToolExecutionError(Exception):
    """Exception raised when a tool execution fails."""
    pass


class ToolNotFoundError(Exception):
    """Exception raised when a tool is not found."""
    pass


def _extract_param_doc(docstring: str, param_name: str) -> Optional[str]:
    """Extract parameter documentation from a docstring."""
    lines = docstring.split('\n')
    for i, line in enumerate(lines):
        if f":param {param_name}:" in line or f"@param {param_name}" in line:
            # Extract the description part
            parts = line.split(':', 2) if ':param' in line else line.split(' ', 2)
            if len(parts) >= 3:
                return parts[2].strip()
    return None


# Decorator for registering tools
def tool(name: Optional[str] = None, description: Optional[str] = None):
    """Decorator to register a function as a tool."""
    def decorator(func):
        registry = ToolRegistry()
        registry.register_function(func, name, description)
        return func
    return decorator
