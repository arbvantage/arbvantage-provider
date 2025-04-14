"""
Action registry and management for provider tasks.

This module implements the action registration and management system that:
1. Defines the structure of provider actions
2. Provides a registry for storing and retrieving actions
3. Handles action registration through decorators
4. Manages action schemas and handlers
5. Implements rate limiting for actions

The module uses type hints and dataclasses for better type safety and code organization.
It supports:
- Action registration with decorators
- Schema validation
- Rate limiting
- Error handling
- Response formatting
"""

from typing import TypeVar, Callable, Dict, Any, Type, Optional
from dataclasses import dataclass
from functools import wraps
from .rate_limit import RateLimitMonitor, TimeBasedRateLimitMonitor, NoRateLimitMonitor
from .schemas import ProviderResponse

T = TypeVar('T')

@dataclass
class Action:
    """
    Data class representing a provider action.
    
    This class holds all the information needed to execute a provider action:
    - Description of what the action does
    - The handler function that implements the action
    - The schema defining the expected payload structure
    - Rate limiting configuration
    
    The class provides:
    1. Action execution with rate limiting
    2. Response formatting
    3. Error handling
    4. Schema validation
    """
    description: str
    handler: Callable
    payload_schema: Dict[str, Type]
    account_schema: Dict[str, Type]
    rate_limit_monitor: Optional[RateLimitMonitor] = None

    def _handle_response(self, response: ProviderResponse) -> Dict[str, Any]:
        """
        Helper method to convert ProviderResponse to dictionary.
        
        This method:
        1. Converts the response to a dictionary
        2. Preserves all response data
        3. Maintains type safety
        
        Args:
            response (ProviderResponse): Response to convert
            
        Returns:
            Dict[str, Any]: Converted response
        """
        return response.model_dump()

    def execute(self, *args, **kwargs) -> Any:
        """
        Execute the action with rate limiting if configured.
        
        This method:
        1. Checks rate limits if configured
        2. Handles throttling if needed
        3. Executes the action handler
        4. Formats the response
        5. Handles errors
        
        Args:
            *args: Positional arguments for the action
            **kwargs: Keyword arguments for the action
            
        Returns:
            Any: Result of the action execution
            
        The method returns:
        - Success response if execution succeeds
        - Rate limit response if limits are exceeded
        - Error response if execution fails
        """
        try:
            if self.rate_limit_monitor:
                # Check rate limits
                limits = self.rate_limit_monitor.check_rate_limits()
                if limits and limits.get("rate_limited"):
                    wait_time = limits.get("wait_time", 1.0)
                    self.rate_limit_monitor.handle_throttling(wait_time)
                    return self._handle_response(ProviderResponse(
                        status="limit",
                        message=f"Rate limit exceeded. Please wait {wait_time} seconds",
                        data={"wait_time": wait_time}
                    ))
                    
                # Execute the action
                result = self.handler(*args, **kwargs)
                
                # Update rate limit after successful execution
                self.rate_limit_monitor.make_safe_request(lambda: None)
                return result
                
            return self.handler(*args, **kwargs)
            
        except Exception as e:
            return self._handle_response(ProviderResponse(
                status="error",
                message="Error executing action",
                data={"error": str(e)}
            ))

class ActionsRegistry:
    """
    Registry for managing provider actions.
    
    This class provides a centralized way to:
    1. Register new actions using decorators
    2. Retrieve actions by name
    3. List all available actions
    4. Validate action parameters
    5. Configure rate limiting
    
    The registry supports:
    - Action registration with decorators
    - Default rate limiting
    - Action-specific rate limiting
    - Custom rate limit monitors
    - Schema validation
    """
    
    def __init__(self):
        """
        Initialize an empty action registry.
        
        Creates a new registry with:
        - Empty action dictionary
        - No default rate limit monitor
        """
        self._actions: Dict[str, Action] = {}
        self._default_rate_limit_monitor: Optional[RateLimitMonitor] = None
    
    def set_default_rate_limit(self, min_delay: float = 1.0) -> None:
        """
        Set default rate limit for all actions.
        
        This method:
        1. Creates a new rate limit monitor
        2. Sets it as the default for all actions
        3. Applies to new actions
        
        Args:
            min_delay: Minimum delay between calls in seconds
        """
        self._default_rate_limit_monitor = NoRateLimitMonitor()
        
    def set_rate_limit(self, action_name: str, min_delay: float = 1.0) -> None:
        """
        Set rate limit for a specific action.
        
        This method:
        1. Finds the action by name
        2. Creates a new rate limit monitor
        3. Sets it for the action
        
        Args:
            action_name: Name of the action to configure
            min_delay: Minimum delay between calls in seconds
        """
        if action_name in self._actions:
            self._actions[action_name].rate_limit_monitor = TimeBasedRateLimitMonitor(min_delay=min_delay)
            
    def set_custom_rate_limit(self, action_name: str, monitor: RateLimitMonitor) -> None:
        """
        Set custom rate limit monitor for a specific action.
        
        This method:
        1. Finds the action by name
        2. Sets the custom monitor
        3. Applies immediately
        
        Args:
            action_name: Name of the action to configure
            monitor: Custom rate limit monitor instance
        """
        if action_name in self._actions:
            self._actions[action_name].rate_limit_monitor = monitor
    
    def register(self, 
                name: str, 
                description: str, 
                payload_schema: Dict[str, Type] = None, 
                account_schema: Dict[str, Type] = None,
                rate_limit_monitor: Optional[RateLimitMonitor] = None):
        """
        Decorator for registering a new action.
        
        This decorator:
        1. Creates a new Action instance
        2. Validates the schema
        3. Sets up rate limiting
        4. Registers the action
        
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
                
            account_schema (Dict[str, Type], optional):
                Dictionary defining the expected account structure.
                If None, an empty dict is used.
                
            rate_limit_monitor (Optional[RateLimitMonitor], optional):
                Custom rate limit monitor for this action.
                If None, the default rate limit monitor will be used.
                
        Returns:
            Callable: A decorator function that registers the action handler.
            
        Example:
            @registry.register(
                name="my_action",
                description="Does something useful",
                payload_schema={"param": str},
                rate_limit_monitor=TimeBasedRateLimitMonitor(min_delay=1.0)
            )
            def my_action(param: str) -> dict:
                return {"result": "success"}
        """
        def wrapper(handler: Callable[..., T]) -> Callable[..., T]:
            self._actions[name] = Action(
                description=description,
                handler=handler,
                payload_schema=payload_schema or {},
                account_schema=account_schema or {},
                rate_limit_monitor=rate_limit_monitor or self._default_rate_limit_monitor
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