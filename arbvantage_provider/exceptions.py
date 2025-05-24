"""
Custom exceptions for the provider service.

This module defines the exception hierarchy for the provider service,
allowing for specific error handling and identification of different types
of failures that can occur during provider operation.

Why is this important?
-----------------------------------
By defining custom exceptions, you can handle different error scenarios in a granular way.
This makes your code more robust, maintainable, and easier to debug.
"""

# Base exception for all provider-related errors.
# Use this as a catch-all for any error that is specific to the provider framework.
class ProviderError(Exception):
    """
    Base exception class for all provider-related errors.
    
    Use this as a catch-all for any error that is specific to the provider framework.
    This allows you to distinguish between framework errors and other exceptions.
    """
    pass

# Exception for when a requested action is not found in the provider.
# Use this to handle cases where a user or system requests an action that is not registered.
class ActionNotFoundError(ProviderError):
    """
    Exception raised when a requested action is not found in the provider.
    
    Use this exception to handle cases where a user or system requests an action
    that is not registered or available in the provider. This helps with debugging
    configuration issues and providing clear error messages to users.
    """
    pass

# Exception for when a task payload fails validation.
# Use this to indicate that the input data for an action is missing required fields or contains invalid values.
class InvalidPayloadError(ProviderError):
    """
    Exception raised when a task payload fails validation.
    
    Use this exception to indicate that the input data for an action is missing required
    fields or contains invalid values. This allows you to return structured validation
    errors and guide users to fix their input.
    """
    pass 