"""
ArbVantage Provider Package

This package provides the core functionality for creating providers that communicate
with the ArbVantage Hub service. It includes:
- Base Provider class for handling Hub communication
- Action registry for managing provider actions
- Rate limit monitoring support
- Common schemas and exceptions

Why is this important?
-----------------------------------
By centralizing all main exports in the __init__.py file, you make it much easier for users
of your package to import what they need with a single import statement. This improves
discoverability, reduces import errors, and makes the codebase easier to maintain.
It also serves as a form of documentation, showing at a glance what the main entry points
of your package are.

Detailed explanation of exports:
- Provider: Main class for building a provider that communicates with the Hub
- Action, ActionsRegistry: System for registering and managing provider actions
- ProviderError, ActionNotFoundError, InvalidPayloadError: Custom exceptions for robust error handling
- hub_pb2, hub_pb2_grpc: gRPC classes generated from protobuf definitions for Hub communication
- ProviderResponse: Pydantic schema for validating and serializing provider responses
- RateLimitMonitor, NoRateLimitMonitor, TimeBasedRateLimitMonitor, AdvancedRateLimitMonitor: Different strategies for rate limiting

If you add new public APIs to the package, make sure to update this file to include them in __all__.
"""

# Import the main Provider class, which is the entry point for building a provider that communicates with the Hub.
from .provider import Provider

# Import the Action class and ActionsRegistry for registering and managing provider actions.
from .actions import Action, ActionsRegistry

# Import custom exceptions for robust error handling in provider logic.
from .exceptions import ProviderError, ActionNotFoundError, InvalidPayloadError

# Import gRPC classes generated from protobuf definitions for Hub communication.
from .protos import hub_pb2, hub_pb2_grpc

# Import the Pydantic schema for validating and serializing provider responses.
from .schemas import ProviderResponse

# Import different strategies for rate limiting.
from .rate_limit import RateLimitMonitor, NoRateLimitMonitor, TimeBasedRateLimitMonitor, AdvancedRateLimitMonitor

# Version of the package.
__version__ = "1.1.8"

# __all__ defines the public API of this module.
# By listing all main exports here, you make it clear what is intended for public use.
# This helps with code completion, documentation, and prevents accidental import of private symbols.
__all__ = [
    'Provider',
    'Action',
    'ActionsRegistry',
    'ProviderError',
    'ActionNotFoundError',
    'InvalidPayloadError',
    'hub_pb2',
    'hub_pb2_grpc',
    'ProviderResponse',
    'RateLimitMonitor',
    'NoRateLimitMonitor',
    'TimeBasedRateLimitMonitor',
    'AdvancedRateLimitMonitor'
] 
