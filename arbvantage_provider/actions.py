"""
Action registry and management for provider tasks.

This module implements the action registration and management system that:
1. Defines the structure of provider actions
2. Provides a registry for storing and retrieving actions
3. Handles action registration through decorators
4. Manages action schemas and handlers

The module uses type hints and dataclasses for better type safety and code organization.
"""

from typing import TypeVar, Callable, Dict, Any, Type
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Action:
    """
    Data class representing a provider action.
    
    This class holds all the information needed to execute a provider action:
    - Description of what the action does
    - The handler function that implements the action
    - The schema defining the expected payload structure
    
    Attributes:
        description (str): 
            Human-readable description of what the action does.
            Used for documentation and help purposes.
            
        handler (Callable): 
            The function that implements the action logic.
            Must be callable and accept the defined payload parameters.
            
        payload_schema (Dict[str, Type]): 
            Dictionary mapping parameter names to their expected types.
            Used for validation of incoming task payloads.
    """
    description: str
    handler: Callable
    payload_schema: Dict[str, Type]
    account_schema: Dict[str, Type]

class ActionsRegistry:
    """
    Registry for managing provider actions.
    
    This class provides a centralized way to:
    1. Register new actions using decorators
    2. Retrieve actions by name
    3. List all available actions
    4. Validate action parameters
    
    The registry maintains a dictionary of action names to Action instances,
    allowing for efficient lookup and management of available actions.
    """
    
    def __init__(self):
        """Initialize an empty action registry."""
        self._actions: Dict[str, Action] = {}
    
    def register(self, name: str, description: str, payload_schema: Dict[str, Type] = None, account_schema: Dict[str, Type] = None):
        """
        Decorator for registering a new action.
        
        This decorator allows for easy registration of new actions with their
        metadata and validation schema. It can be used as a function decorator
        to register action handlers.
        
        Args:
            name (str): 
                Unique identifier for the action.
                Used to look up the action when processing tasks.
                
            description (str): 
                Human-readable description of what the action does.
                Used for documentation purposes.
                
            payload_schema (Dict[str, Type], optional): 
                Dictionary defining the expected payload structure.
                If None, an empty dict is used.
                
        Returns:
            Callable: A decorator function that registers the action handler.
        """
        def wrapper(handler: Callable[..., T]) -> Callable[..., T]:
            self._actions[name] = Action(
                description=description,
                handler=handler,
                payload_schema=payload_schema or {},
                account_schema=account_schema or {} 
            )
            return handler
        return wrapper

    def get_action(self, name: str) -> Action:
        """
        Retrieve an action by its name.
        
        Args:
            name (str): The name of the action to retrieve.
            
        Returns:
            Action: The action instance if found, None otherwise.
        """
        return self._actions.get(name)

    def get_all_actions(self) -> Dict[str, Action]:
        """
        Get all registered actions.
        
        Returns:
            Dict[str, Action]: Dictionary mapping action names to their instances.
        """
        return self._actions 