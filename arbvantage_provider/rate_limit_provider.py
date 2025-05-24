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

# Import typing for type hints and flexibility in monitor selection.
from typing import Dict, Any, Optional, Type
# Import all available rate limit monitor classes for flexible strategy selection.
from .rate_limit import (
    RateLimitMonitor,
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor,
    CustomRateLimitMonitor,
    NoRateLimitMonitor
)

class RateLimitProvider:
    """
    High-level provider for managing rate limiting strategies and configurations.
    
    This class acts as a wrapper around different rate limit monitor implementations.
    It allows you to:
    - Choose a rate limiting strategy (time-based, advanced, custom, or none)
    - Configure and update rate limiting parameters at runtime
    - Safely execute requests with automatic rate limit checks
    - Retrieve and update current configuration
    
    Why is this important?
    -----------------------------------
    Centralizing rate limit logic in a dedicated provider makes your code modular and testable.
    You can easily swap out strategies or update configuration without changing business logic.
    This is especially useful for APIs with changing or complex rate limit requirements.
    """
    
    def __init__(
        self,
        monitor_class: Type[RateLimitMonitor] = NoRateLimitMonitor,
        **monitor_kwargs
    ):
        """
        Initialize the RateLimitProvider with a specific rate limit monitor class and configuration.
        
        Args:
            monitor_class (Type[RateLimitMonitor]): The class of rate limit monitor to use.
            **monitor_kwargs: Configuration parameters for the monitor class.
        
        Example usage:
            # No rate limiting (default)
            provider = RateLimitProvider()
            
            # Time-based rate limiting
            provider = RateLimitProvider(
                monitor_class=TimeBasedRateLimitMonitor,
                min_delay=1.0,
                max_calls_per_second=1
            )
        """
        # Create the monitor instance using the provided class and configuration.
        self.monitor = monitor_class(**monitor_kwargs)
        # Store the configuration for future reference or updates.
        self._config = monitor_kwargs
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check if the current rate limit is exceeded.
        
        Returns:
            Optional[Dict[str, Any]]: Rate limit information if exceeded, None otherwise.
        
        This method is useful for checking limits before making expensive API calls.
        """
        # Delegate the check to the underlying monitor.
        return self.monitor.check_rate_limits()
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Execute a request function with rate limit checks and throttling if needed.
        
        Args:
            request_func (callable): The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.
        
        Returns:
            Any: The result of the request function.
        
        This method ensures you never exceed API limits and can handle rate limit errors gracefully.
        """
        # Delegate the safe execution to the monitor.
        return self.monitor.make_safe_request(request_func, *args, **kwargs)
        
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current rate limit configuration as a dictionary.
        
        Returns:
            Dict[str, Any]: The current configuration.
        
        Useful for saving, restoring, or inspecting the current settings.
        """
        # Return a copy of the configuration to prevent accidental modification.
        return self._config.copy()
        
    def update_config(self, **new_config) -> None:
        """
        Update the rate limit configuration and recreate the monitor with new settings.
        
        Args:
            **new_config: New configuration values to update.
        
        Example usage:
            provider.update_config(
                min_delay=2.0,
                max_calls_per_second=2
            )
        """
        # Update the configuration dictionary.
        self._config.update(new_config)
        # Recreate the monitor with the new configuration.
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