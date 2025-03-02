from typing import TypeVar, Callable, Dict, Any, Type
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Action:
    """Class for describing a provider action"""
    description: str
    handler: Callable
    payload_schema: Dict[str, Type]

class ActionsRegistry:
    """Registry of provider actions"""
    def __init__(self):
        self._actions: Dict[str, Action] = {}
    
    def register(self, name: str, description: str, payload_schema: Dict[str, Type] = None):
        """Decorator for registering a new action"""
        def wrapper(handler: Callable[..., T]) -> Callable[..., T]:
            self._actions[name] = Action(
                description=description,
                handler=handler,
                payload_schema=payload_schema or {}
            )
            return handler
        return wrapper

    def get_action(self, name: str) -> Action:
        """Get an action by name"""
        return self._actions.get(name)

    def get_all_actions(self) -> Dict[str, Action]:
        """Get all registered actions"""
        return self._actions 