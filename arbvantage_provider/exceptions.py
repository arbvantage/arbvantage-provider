class ProviderError(Exception):
    """Base class for provider exceptions"""
    pass

class ActionNotFoundError(ProviderError):
    """Raised when the requested action is not found"""
    pass

class InvalidPayloadError(ProviderError):
    """Raised when the payload is invalid"""
    pass 