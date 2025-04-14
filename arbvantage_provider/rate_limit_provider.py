"""
Rate limit provider implementation.

This module provides rate limiting functionality for providers.
It supports multiple rate limiting strategies and configurations.
"""

from typing import Dict, Any, Optional, Type
from .rate_limit import (
    RateLimitMonitor,
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor,
    CustomRateLimitMonitor,
    DEFAULT_RATE_LIMIT_MONITOR
)

class RateLimitProvider:
    """
    Provider for rate limiting functionality.
    Manages rate limit monitors and configurations.
    """
    
    def __init__(
        self,
        monitor_class: Type[RateLimitMonitor] = DEFAULT_RATE_LIMIT_MONITOR.__class__,
        **monitor_kwargs
    ):
        """
        Initialize rate limit provider.
        
        Args:
            monitor_class (Type[RateLimitMonitor]): Class of rate limit monitor to use
            **monitor_kwargs: Arguments to pass to monitor constructor
        """
        self.monitor = monitor_class(**monitor_kwargs)
        self._config = monitor_kwargs
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check current rate limits.
        
        Returns:
            Optional[Dict[str, Any]]: Rate limit information if exceeded, None otherwise
        """
        return self.monitor.check_rate_limits()
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Execute request with rate limit consideration.
        
        Args:
            request_func (callable): Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the request function
        """
        return self.monitor.make_safe_request(request_func, *args, **kwargs)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get current rate limit configuration.
        
        Returns:
            Dict[str, Any]: Current configuration
        """
        return self._config.copy()
        
    def update_config(self, **new_config) -> None:
        """
        Update rate limit configuration.
        
        Args:
            **new_config: New configuration values
        """
        self._config.update(new_config)
        # Recreate monitor with new config
        self.monitor = self.monitor.__class__(**self._config)

# Example usage:
"""
# Global rate limiting
provider = RateLimitProvider(
    monitor_class=TimeBasedRateLimitMonitor,
    min_delay=1.0,
    max_calls_per_second=1
)

# API-specific rate limiting
class FacebookProvider(RateLimitProvider):
    def __init__(self):
        super().__init__(
            monitor_class=AdvancedRateLimitMonitor,
            min_delay=0.5,
            max_calls_per_second=2,
            warning_threshold=0.8,
            critical_threshold=0.9
        )

# Custom rate limiting with sliding window
class CustomProvider(RateLimitProvider):
    def __init__(self):
        super().__init__(
            monitor_class=CustomRateLimitMonitor,
            window_size=60,
            max_requests=100
        )
""" 