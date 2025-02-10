class ProviderError(Exception):
    """Базовый класс для исключений провайдера"""
    pass

class ActionNotFoundError(ProviderError):
    """Вызывается когда запрошенное действие не найдено"""
    pass

class InvalidPayloadError(ProviderError):
    """Вызывается при неверных параметрах в payload"""
    pass 