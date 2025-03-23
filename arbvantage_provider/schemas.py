"""
Schema definitions for provider responses and data validation.

This module defines the data structures and validation rules for:
- Provider task responses
- Response status types
- Additional data payloads

The schemas are implemented using Pydantic for automatic validation and serialization.
"""

from typing import Any, Literal, Optional
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
            
        message (str): 
            Human-readable description of the result.
            Must be non-empty and provide clear information about the outcome.
            
        data (Optional[dict[str, Any]]): 
            Additional result data in key-value format.
            Optional field for providing extra information about the task result.
    """
    status: Literal['success', 'error', 'warning']
    message: str = Field(..., min_length=1, description="Human readable result message")
    data: Optional[dict[str, Any]] = Field(default=None, description="Additional result data") 