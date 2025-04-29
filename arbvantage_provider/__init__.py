"""
ArbVantage Provider Package

This package provides the core functionality for creating providers that communicate
with the ArbVantage Hub service. It includes:
- Base Provider class for handling Hub communication
- Action registry for managing provider actions
- Rate limit monitoring support
- Common schemas and exceptions
"""

from .provider import Provider
from .actions import Action, ActionsRegistry
from .exceptions import ProviderError, ActionNotFoundError, InvalidPayloadError
from .protos import hub_pb2, hub_pb2_grpc
from .schemas import ProviderResponse
from .rate_limit import RateLimitMonitor, NoRateLimitMonitor, TimeBasedRateLimitMonitor, AdvancedRateLimitMonitor

__version__ = "1.0.8"

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
