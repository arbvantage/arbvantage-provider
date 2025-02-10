from typing import TypeVar, Callable, Dict, Any, Type
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class Action:
    """Класс для описания действия провайдера"""
    description: str
    handler: Callable
    payload_schema: Dict[str, Type]

class ActionsRegistry:
    """Реестр действий провайдера"""
    def __init__(self):
        self._actions: Dict[str, Action] = {}
    
    def register(self, name: str, description: str, payload_schema: Dict[str, Type] = None):
        """Декоратор для регистрации нового действия"""
        def wrapper(handler: Callable[..., T]) -> Callable[..., T]:
            self._actions[name] = Action(
                description=description,
                handler=handler,
                payload_schema=payload_schema or {}
            )
            return handler
        return wrapper

    def get_action(self, name: str) -> Action:
        """Получить действие по имени"""
        return self._actions.get(name)

    def get_all_actions(self) -> Dict[str, Action]:
        """Получить все зарегистрированные действия"""
        return self._actions 