"""
Rate limiting implementation for the provider framework.

This module provides several rate limiting strategies:
1. Time-based rate limiting with fixed delays
2. Advanced rate limiting with warning thresholds
3. Custom rate limiting with sliding window approach
4. No rate limiting (pass-through implementation)

The rate limiting system is designed to be:
- Thread-safe: All operations are protected by locks
- Extensible: Easy to add new rate limiting strategies
- Configurable: Flexible parameters for each strategy
- Observable: Detailed logging and metrics
- Performant: Minimal overhead when not rate limited
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
import threading
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class RateLimitMonitor(ABC):
    """
    Abstract base class for rate limit monitors.
    Implement this class to create custom rate limiting strategies.
    
    This class defines the interface that all rate limit monitors must implement:
    - check_rate_limits(): Check if rate limit is exceeded
    - handle_throttling(): Handle throttling when limit is exceeded
    - make_safe_request(): Execute request with rate limit consideration
    
    Subclasses should implement these methods according to their specific
    rate limiting strategy while maintaining thread safety.
    """
    
    @abstractmethod
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check if rate limit is exceeded.
        
        This method should:
        1. Check current usage against limits
        2. Return None if within limits
        3. Return rate limit info if exceeded
        
        Returns:
            Optional[Dict[str, Any]]: Rate limit information if exceeded, None otherwise
            The dictionary should contain at least:
            - rate_limited: bool
            - wait_time: float (seconds to wait)
            - current_count: int
            - limit: int
        """
        pass
        
    @abstractmethod
    def handle_throttling(self, wait_time: int) -> None:
        """
        Handle throttling when rate limit is exceeded.
        
        This method should:
        1. Implement the waiting strategy
        2. Log throttling events
        3. Update internal state if needed
        
        Args:
            wait_time (int): Time to wait in seconds
        """
        pass
        
    @abstractmethod
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Execute request with rate limit consideration.
        
        This method should:
        1. Check rate limits
        2. Handle throttling if needed
        3. Execute the request
        4. Update internal state
        
        Args:
            request_func (callable): Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the request function
        """
        pass

class TimeBasedRateLimitMonitor(RateLimitMonitor):
    """
    Simple time-based rate limit monitor.
    Uses fixed delays between requests.
    """
    
    def __init__(self, min_delay: float = 1.0, max_calls_per_second: int = 1, timezone: str = "UTC"):
        """
        Initialize time-based rate limit monitor.
        
        Args:
            min_delay (float): Minimum delay between requests in seconds
            max_calls_per_second (int): Maximum number of calls per second
            timezone (str): Timezone for rate limiting
        """
        self.min_delay = min_delay
        self.max_calls_per_second = max_calls_per_second
        self.timezone = timezone
        self._last_request_time = 0
        self._lock = threading.Lock()
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self.min_delay:
            return {
                "rate_limited": True,
                "wait_time": self.min_delay - time_since_last,
                "current_count": 1,
                "limit": self.max_calls_per_second
            }
            
        return None
        
    def handle_throttling(self, wait_time: int) -> None:
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        with self._lock:
            limits = self.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.handle_throttling(limits["wait_time"])
                
            self._last_request_time = time.time()
            return request_func(*args, **kwargs)

class AdvancedRateLimitMonitor(RateLimitMonitor):
    """
    Advanced rate limit monitor with warning thresholds.
    Provides early warnings when approaching rate limits.
    """
    
    def __init__(
        self,
        min_delay: float = 1.0,
        max_calls_per_second: int = 1,
        warning_threshold: float = 0.8,
        critical_threshold: float = 0.9
    ):
        """
        Initialize advanced rate limit monitor.
        
        Args:
            min_delay (float): Minimum delay between requests
            max_calls_per_second (int): Maximum calls per second
            warning_threshold (float): Percentage of limit that triggers warning
            critical_threshold (float): Percentage of limit that triggers critical alert
        """
        self.min_delay = min_delay
        self.max_calls_per_second = max_calls_per_second
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self._request_count = 0
        self._window_start = time.time()
        self._lock = threading.Lock()
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        window_duration = current_time - self._window_start
        
        if window_duration >= 1.0:
            self._request_count = 0
            self._window_start = current_time
            
        self._request_count += 1
        rate = self._request_count / window_duration if window_duration > 0 else 0
        
        if rate >= self.max_calls_per_second:
            return {
                "rate_limited": True,
                "wait_time": 1.0,
                "current_count": self._request_count,
                "limit": self.max_calls_per_second,
                "rate": rate
            }
            
        if rate >= self.max_calls_per_second * self.critical_threshold:
            logger.warning(f"Critical rate limit threshold reached: {rate:.2f} requests/second")
        elif rate >= self.max_calls_per_second * self.warning_threshold:
            logger.warning(f"Warning rate limit threshold reached: {rate:.2f} requests/second")
            
        return None
        
    def handle_throttling(self, wait_time: int) -> None:
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        with self._lock:
            limits = self.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.handle_throttling(limits["wait_time"])
            return request_func(*args, **kwargs)

class CustomRateLimitMonitor(RateLimitMonitor):
    """
    Custom rate limit monitor with sliding window approach.
    Provides more granular control over rate limiting.
    """
    
    def __init__(self, window_size: int = 60, max_requests: int = 100):
        """
        Initialize custom rate limit monitor.
        
        Args:
            window_size (int): Size of the sliding window in seconds
            max_requests (int): Maximum number of requests per window
        """
        self.window_size = window_size
        self.max_requests = max_requests
        self._requests = []
        self._lock = threading.Lock()
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        
        with self._lock:
            # Remove old requests
            self._requests = [t for t in self._requests if current_time - t < self.window_size]
            
            if len(self._requests) >= self.max_requests:
                oldest_request = self._requests[0]
                wait_time = self.window_size - (current_time - oldest_request)
                return {
                    "rate_limited": True,
                    "wait_time": wait_time,
                    "current_count": len(self._requests),
                    "limit": self.max_requests
                }
                
            self._requests.append(current_time)
            return None
            
    def handle_throttling(self, wait_time: int) -> None:
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        limits = self.check_rate_limits()
        if limits and limits.get("rate_limited"):
            self.handle_throttling(limits["wait_time"])
        return request_func(*args, **kwargs)

class NoRateLimitMonitor(RateLimitMonitor):
    """
    Rate limit monitor that never limits requests.
    This is a pass-through implementation that allows all requests.
    
    This monitor is useful when:
    1. No rate limiting is needed
    2. Rate limiting is handled externally
    3. Testing and development
    4. High-performance scenarios
    
    The monitor implements all required methods but:
    - Never returns rate limit information
    - Never throttles requests
    - Simply passes through all requests
    
    This is the default monitor for new providers and actions.
    """
    
    def __init__(self):
        """
        Initialize the no-rate-limit monitor.
        
        This implementation doesn't require any configuration or state.
        It's designed to be lightweight and have zero overhead.
        """
        pass
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check if rate limit is exceeded.
        
        This implementation never limits requests, so always returns None.
        It's a pure pass-through with no state or checks.
        
        Returns:
            None: Always returns None to indicate no rate limiting
        """
        return None
        
    def handle_throttling(self, wait_time: int) -> None:
        """
        Handle throttling when rate limit is exceeded.
        
        This implementation does nothing as there are no rate limits.
        The wait_time parameter is ignored.
        
        Args:
            wait_time (int): Time to wait in seconds (ignored)
        """
        pass
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Execute request with rate limit consideration.
        
        This implementation simply executes the request without any
        rate limiting or throttling. It's a pure pass-through.
        
        Args:
            request_func (callable): Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the request function
        """
        return request_func(*args, **kwargs) 