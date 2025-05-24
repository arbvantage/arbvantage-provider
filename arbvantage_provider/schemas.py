"""
Schema definitions for provider responses and data validation.

This module defines the data structures and validation rules for:
- Provider task responses
- Response status types
- Additional data payloads

The schemas are implemented using Pydantic for automatic validation and serialization.

Why is this important?
-----------------------------------
Using strict schemas ensures that all responses are predictable and easy to validate.
This improves reliability, reduces bugs, and makes integration with external systems easier.
"""

# Import typing for type hints and Literal for strict value constraints.
from typing import Any, Literal, Optional
# Import BaseModel and Field from Pydantic for schema definition and validation.
from pydantic import BaseModel, Field

class ProviderResponse(BaseModel):
    """
    Schema for validating provider task results.
    
    This schema ensures that all provider responses follow a consistent format
    and contain the required information for task processing.
    
    Attributes:
        status (Literal['success', 'error', 'warning']): 
            The result status of the task execution.
            - 'success': Task completed successfully
            - 'error': Task failed with an error
            - 'warning': Task completed with warnings
            # Use Literal to restrict allowed values for better validation.
        
        message (str): 
            Human-readable description of the result.
            Must be non-empty and provide clear information about the outcome.
            # Use Field to enforce minimum length and add description for documentation.
        
        data (Optional[dict[str, Any]]): 
            Additional result data in key-value format.
            Optional field for providing extra information about the task result.
            # This allows you to include any extra context or results as needed.
    
    Why is this important?
    -----------------------------------
    By using a strict schema (with Pydantic), you ensure that all responses
    are predictable and easy to validate, both for your own code and for
    any external systems (like the Hub) that consume your responses.
    This reduces bugs, makes integration easier, and improves reliability.
    """
    # Status of the response: must be 'success', 'error', or 'warning'.
    status: Literal['success', 'error', 'warning']
    # Human readable result message, required and must be at least 1 character.
    message: str = Field(..., min_length=1, description="Human readable result message")
    # Optional additional result data as a dictionary.
    data: Optional[dict[str, Any]] = Field(default=None, description="Additional result data") 