"""
Rate Limit Provider Example

This example demonstrates various approaches to rate limiting in providers using the Arbvantage Provider Framework.
It shows how to:
1. Use global, action-specific, and custom rate limit monitors
2. Register actions with different rate limiting strategies
3. Implement a custom rate limit monitor

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "rate-limit-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")

Why is this important?
-----------------------------------
Correct rate limiting is critical for API safety, compliance, and fair usage. This example shows how to use and extend the framework's rate limiting features.
"""

from typing import Dict, Any, Optional
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import (
    RateLimitMonitor,
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor
)
import time
import threading

class CustomRateLimitMonitor(RateLimitMonitor):
    """
    Custom rate limit monitor implementation using a sliding window approach.
    This monitor is thread-safe and can be used for more granular rate limiting.
    """
    
    def __init__(self, max_requests: int = 100, window_size: int = 60):
        """
        Initialize the rate limit monitor.
        
        Args:
            max_requests: Maximum number of requests allowed in the window
            window_size: Time window size in seconds
        """
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = []
        self.lock = threading.Lock()
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        """
        Check if rate limit is exceeded.
        Returns rate limit information if exceeded, None otherwise.
        """
        current_time = time.time()
        
        with self.lock:
            # Remove old requests outside the window
            self.requests = [t for t in self.requests 
                           if current_time - t < self.window_size]
            
            if len(self.requests) >= self.max_requests:
                # Calculate wait time until oldest request expires
                wait_time = self.window_size - (current_time - self.requests[0])
                return {
                    "rate_limited": True,
                    "wait_time": wait_time,
                    "current_count": len(self.requests),
                    "limit": self.max_requests
                }
                
        return None
        
    def handle_throttling(self, wait_time: int = 60) -> None:
        """
        Handle rate limit throttling by waiting.
        
        Args:
            wait_time: Time to wait in seconds
        """
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        """
        Execute request with rate limit consideration.
        
        Args:
            request_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Result of the request function
        """
        limits = self.check_rate_limits()
        if limits and limits.get("rate_limited"):
            self.handle_throttling(limits["wait_time"])
            
        with self.lock:
            self.requests.append(time.time())
            
        return request_func(*args, **kwargs)

class RateLimitProvider(Provider):
    """
    Example provider demonstrating different rate limiting approaches.
    This provider shows how to implement rate limiting at different levels.
    
    Why is this important?
    -----------------------------------
    Shows how to use global, action-specific, and custom rate limit monitors in practice.
    """
    
    def __init__(self):
        """
        Initialize the provider with different rate limit monitors.
        """
        # Global rate limit for all requests
        global_rate_limit = TimeBasedRateLimitMonitor(
            min_delay=1.0,              # Minimum delay between requests
            max_calls_per_second=2,     # Maximum calls per second
            timezone="UTC"              # Timezone for rate limiting
        )
        
        super().__init__(
            name="rate-limit-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=global_rate_limit
        )
        
        # Action-specific rate limit
        self.api_rate_limit = AdvancedRateLimitMonitor(
            min_delay=0.5,              # Faster rate limit for API calls
            max_calls_per_second=5,     # Higher limit for API calls
            warning_threshold=0.8,      # 80% of limit triggers warning
            critical_threshold=0.9      # 90% of limit triggers critical alert
        )
        
        # Custom rate limit for specific actions
        self.custom_rate_limit = CustomRateLimitMonitor(
            max_requests=50,            # 50 requests per minute
            window_size=60              # 1 minute window
        )
        
        # Register actions with different rate limits
        self._register_actions()
        
    def _register_actions(self):
        """
        Register provider actions with different rate limiting strategies.
        """
        @self.actions.register(
            name="global_limited_action",
            description="Action using global rate limit",
            payload_schema={"param": str}
        )
        def global_limited_action(payload: dict) -> dict:
            """
            Action using the provider's global rate limit.
            
            Args:
                payload: Action payload (must contain 'param')
            Returns:
                Action result
            """
            return {"result": "global_limited"}
            
        @self.actions.register(
            name="api_action",
            description="Action with API-specific rate limit",
            payload_schema={"endpoint": str, "params": dict},
            rate_limit_monitor=self.api_rate_limit
        )
        def api_action(payload: dict) -> dict:
            """
            Action with API-specific rate limit.
            
            Args:
                payload: Action payload containing endpoint and parameters
            Returns:
                API call result
            """
            # Check API rate limit
            limits = self.api_rate_limit.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.api_rate_limit.handle_throttling(limits["wait_time"])
                
            # Make API call
            try:
                result = self._make_api_call(payload["endpoint"], payload["params"])
                return {"status": "success", "data": result}
            except Exception as e:
                return {"status": "error", "message": str(e)}
                
        @self.actions.register(
            name="custom_limited_action",
            description="Action with custom rate limit",
            payload_schema={"param": str},
            rate_limit_monitor=self.custom_rate_limit
        )
        def custom_limited_action(payload: dict) -> dict:
            """
            Action using custom rate limit monitor.
            
            Args:
                payload: Action payload (must contain 'param')
            Returns:
                Action result
            """
            return {"result": "custom_limited"}
            
    def _make_api_call(self, endpoint: str, params: dict) -> dict:
        """
        Make an API call with rate limit consideration.
        
        Args:
            endpoint: API endpoint
            params: Request parameters
        Returns:
            API response
        """
        # Simulate API call
        time.sleep(0.1)
        return {"endpoint": endpoint, "params": params}

if __name__ == "__main__":
    """
    Run the provider if this script is executed directly.
    
    Why is this important?
    -----------------------------------
    This allows you to test rate limiting strategies in isolation before integrating with the hub.
    """
    provider = RateLimitProvider()
    provider.start() 