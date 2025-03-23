"""
Custom exceptions for the provider service.

This module defines the exception hierarchy for the provider service,
allowing for specific error handling and identification of different types
of failures that can occur during provider operation.
"""

class ProviderError(Exception):
    """
    Base exception class for all provider-related errors.
    
    This is the root exception class that all other provider-specific
    exceptions should inherit from. It provides a common base for
    error handling and identification of provider-related issues.
    """
    pass

class ActionNotFoundError(ProviderError):
    """
    Exception raised when a requested action is not found in the provider.
    
    This exception is used when a task requests an action that hasn't been
    registered with the provider's action registry. It helps identify
    configuration issues or invalid task requests.
    """
    pass

class InvalidPayloadError(ProviderError):
    """
    Exception raised when a task payload fails validation.
    
    This exception is used when the payload data for a task doesn't meet
    the required schema or validation rules. It helps identify data format
    issues or missing required fields in task requests.
    """
    pass 