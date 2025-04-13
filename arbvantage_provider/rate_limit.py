"""
Rate Limit Support for Providers

This module adds optional rate limit support to the base Provider class.
It provides an abstract interface for rate limit monitoring and handling,
but allows providers to work without rate limit monitoring if needed.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Union
import logging
import os
import time

logger = logging.getLogger(__name__)

class RateLimitMonitor(ABC):
    """
    Abstract base class for rate limit monitoring
    
    This class defines the interface for rate limit monitoring implementations.
    Each provider can implement its own monitoring logic.
    """
    
    @abstractmethod
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check current rate limits
        
        Returns:
            Dictionary containing rate limit information or None if check failed
        """
        pass
        
    @abstractmethod
    def handle_throttling(self, wait_time: int = 60) -> None:
        """
        Handle rate limit exceeded
        
        Args:
            wait_time: Time to wait in seconds when limits are exceeded
        """
        pass
        
    @abstractmethod
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Make a request with rate limit consideration
        
        Args:
            request_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the request function
        """
        pass

class NoRateLimitMonitor(RateLimitMonitor):
    """
    Dummy rate limit monitor that does nothing
    
    This class implements the RateLimitMonitor interface but performs no actual
    rate limit monitoring. It can be used by providers that don't need rate limit handling.
    """
    
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """No rate limit checking"""
        return None
        
    def handle_throttling(self, wait_time: int = 60) -> None:
        """No throttling handling"""
        pass
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """Just execute the request without any rate limit handling"""
        return request_func(*args, **kwargs)

class TimeBasedRateLimitMonitor(RateLimitMonitor):
    """
    Rate limit monitor that uses time-based throttling
    
    This implementation uses a time-based approach to rate limiting,
    ensuring a minimum delay between consecutive requests.
    """
    
    def __init__(self, min_delay: float = 1.0):
        """
        Initialize the time-based rate limit monitor
        
        Args:
            min_delay: Minimum delay between requests in seconds
        """
        self.min_delay = min_delay
        self.last_request_time = 0
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """Check if we need to wait before next request"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            return {
                "wait_time": self.min_delay - time_since_last,
                "rate_limited": True
            }
        return None
        
    def handle_throttling(self, wait_time: int = 60) -> None:
        """Wait for the specified time"""
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """Execute request with rate limit consideration"""
        limits = self.check_rate_limits()
        if limits and limits.get("rate_limited"):
            self.handle_throttling(limits["wait_time"])
            
        result = request_func(*args, **kwargs)
        self.last_request_time = time.time()
        return result 

class AdvancedRateLimitMonitor(RateLimitMonitor):
    """
    Advanced rate limit monitor with multiple metrics tracking
    
    This implementation provides sophisticated rate limiting capabilities similar to major APIs like Facebook.
    It can track multiple metrics (calls, CPU, time) and handle complex throttling scenarios.
    """
    
    def __init__(self, 
                 min_delay: float = 1.0,
                 max_calls_per_second: int = 2,
                 warning_threshold: float = 0.8,
                 critical_threshold: float = 0.9):
        """
        Initialize the advanced rate limit monitor
        
        Args:
            min_delay: Minimum delay between requests in seconds
            max_calls_per_second: Maximum number of calls allowed per second
            warning_threshold: Threshold for warning level (0.0 to 1.0)
            critical_threshold: Threshold for critical level (0.0 to 1.0)
        """
        self.min_delay = min_delay
        self.max_calls_per_second = max_calls_per_second
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        
        self.last_request_time = 0
        self.call_count = 0
        self.metrics = {
            'call_count': 0,
            'total_time': 0,
            'total_cpu': 0
        }
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check current rate limits with detailed metrics
        
        Returns:
            Dictionary containing detailed rate limit information or None if check failed
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Calculate usage percentages
        call_usage = self.metrics['call_count'] / 100  # Assuming 100 as max calls
        cpu_usage = self.metrics['total_cpu'] / 100    # Assuming 100 as max CPU
        
        # Check if we're approaching limits
        is_near_limit = (call_usage > self.warning_threshold or 
                        cpu_usage > self.warning_threshold)
        
        # Check if we've exceeded critical limits
        is_critical = (call_usage > self.critical_threshold or 
                      cpu_usage > self.critical_threshold)
        
        if time_since_last < self.min_delay or is_critical:
            return {
                "wait_time": max(self.min_delay - time_since_last, 1.0),
                "rate_limited": True,
                "metrics": self.metrics,
                "is_near_limit": is_near_limit,
                "is_critical": is_critical
            }
        return None
        
    def handle_throttling(self, wait_time: int = 60) -> None:
        """
        Handle rate limit exceeded with adaptive waiting
        
        Args:
            wait_time: Base time to wait in seconds when limits are exceeded
        """
        # Reset metrics after throttling
        self.metrics = {
            'call_count': 0,
            'total_time': 0,
            'total_cpu': 0
        }
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Make a request with advanced rate limit consideration
        
        Args:
            request_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the request function
        """
        while True:
            limits = self.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.handle_throttling(limits["wait_time"])
                continue
                
            try:
                start_time = time.time()
                result = request_func(*args, **kwargs)
                end_time = time.time()
                
                # Update metrics
                self.metrics['call_count'] += 1
                self.metrics['total_time'] += (end_time - start_time)
                self.metrics['total_cpu'] += (end_time - start_time) * 100  # Simplified CPU metric
                
                self.last_request_time = time.time()
                return result
                
            except Exception as e:
                if "rate limit" in str(e).lower():
                    self.handle_throttling()
                    continue
                raise e 