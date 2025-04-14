"""
Rate limit provider implementation.

This module provides rate limiting functionality for providers.
It supports multiple rate limiting strategies and configurations.

The rate limit provider is designed to:
1. Manage rate limit monitors and their configurations
2. Provide a clean interface for rate limiting operations
3. Support different rate limiting strategies
4. Handle configuration updates
5. Provide monitoring and metrics

Key features:
- Thread-safe operations
- Flexible configuration
- Multiple rate limiting strategies
- Easy to extend
- Detailed logging
"""

from typing import Dict, Any, Optional, Type
from .rate_limit import (
    RateLimitMonitor,
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor,
    CustomRateLimitMonitor,
    NoRateLimitMonitor
)

class RateLimitProvider:
    """
    Provider for rate limiting functionality.
    Manages rate limit monitors and configurations.
    
    This class provides a high-level interface for rate limiting:
    1. Initialization with different monitor types
    2. Configuration management
    3. Rate limit checking
    4. Safe request execution
    5. Monitoring and metrics
    
    The provider supports multiple rate limiting strategies:
    - Time-based rate limiting
    - Advanced rate limiting with thresholds
    - Custom rate limiting with sliding window
    - No rate limiting (pass-through)
    
    By default, it uses NoRateLimitMonitor to avoid
    unnecessary overhead when rate limiting is not needed.
    """
    
    def __init__(
        self,
        monitor_class: Type[RateLimitMonitor] = NoRateLimitMonitor,
        **monitor_kwargs
    ):
        """
        Initialize rate limit provider.
        
        Args:
            monitor_class (Type[RateLimitMonitor]): 
                Class of rate limit monitor to use.
                Defaults to NoRateLimitMonitor for no rate limiting.
                
            **monitor_kwargs: 
                Arguments to pass to monitor constructor.
                These depend on the specific monitor class.
                
        Example:
            # No rate limiting (default)
            provider = RateLimitProvider()
            
            # Time-based rate limiting
            provider = RateLimitProvider(
                monitor_class=TimeBasedRateLimitMonitor,
                min_delay=1.0,
                max_calls_per_second=1
            )
            
            # Advanced rate limiting
            provider = RateLimitProvider(
                monitor_class=AdvancedRateLimitMonitor,
                min_delay=0.5,
                max_calls_per_second=2,
                warning_threshold=0.8,
                critical_threshold=0.9
            )
        """
        self.monitor = monitor_class(**monitor_kwargs)
        self._config = monitor_kwargs
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check current rate limits.
        
        This method:
        1. Delegates to the underlying monitor
        2. Returns rate limit information if exceeded
        3. Returns None if within limits
        
        Returns:
            Optional[Dict[str, Any]]: 
                Rate limit information if exceeded, None otherwise.
                The structure depends on the monitor type.
        """
        return self.monitor.check_rate_limits()
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Execute request with rate limit consideration.
        
        This method:
        1. Checks rate limits
        2. Handles throttling if needed
        3. Executes the request
        4. Returns the result
        
        Args:
            request_func (callable): Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the request function
            
        Example:
            result = provider.make_safe_request(
                my_api_call,
                arg1,
                arg2,
                param1=value1,
                param2=value2
            )
        """
        return self.monitor.make_safe_request(request_func, *args, **kwargs)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get current rate limit configuration.
        
        Returns:
            Dict[str, Any]: 
                Current configuration as a dictionary.
                This can be used to save/restore configuration.
        """
        return self._config.copy()
        
    def update_config(self, **new_config) -> None:
        """
        Update rate limit configuration.
        
        This method:
        1. Updates the configuration
        2. Recreates the monitor with new settings
        3. Preserves the monitor type
        
        Args:
            **new_config: New configuration values
            
        Example:
            provider.update_config(
                min_delay=2.0,
                max_calls_per_second=2
            )
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