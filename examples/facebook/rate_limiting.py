"""
Rate Limiting Strategies Example

This example demonstrates different rate limiting strategies for Facebook API.
It shows how to:
1. Use different rate limit monitors
2. Configure rate limits for different actions
3. Handle rate limit errors
4. Implement custom rate limiting logic
"""

from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import (
    AdvancedRateLimitMonitor,
    TimeBasedRateLimitMonitor,
    NoRateLimitMonitor
)
from arbvantage_provider.schemas import ProviderResponse
import os
import time
from typing import Dict, Any

class RateLimitProvider(Provider):
    """
    Rate limiting strategies provider example.
    
    This provider demonstrates different approaches to rate limiting:
    - Advanced rate limiting with multiple metrics
    - Time-based rate limiting
    - No rate limiting
    - Custom rate limit handling
    """
    
    def __init__(self):
        """
        Initialize the rate limiting provider.
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "rate-limit-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Example 1: Action with advanced rate limiting
        @self.actions.register(
            name="advanced_action",
            description="Action with advanced rate limiting",
            payload_schema={
                "param": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            },
            rate_limit_monitor=AdvancedRateLimitMonitor(
                min_delay=1.0,
                max_calls_per_second=2,
                warning_threshold=0.8,
                critical_threshold=0.9
            )
        )
        def advanced_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action with sophisticated rate limiting using multiple metrics.
            """
            # In a real implementation, this would call Facebook API
            return ProviderResponse(
                status="success",
                data={
                    "param": payload["param"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
        # Example 2: Action with time-based rate limiting
        @self.actions.register(
            name="time_based_action",
            description="Action with time-based rate limiting",
            payload_schema={
                "param": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            },
            rate_limit_monitor=TimeBasedRateLimitMonitor(
                min_delay=2.0,  # 2 seconds between requests
                timezone="UTC"
            )
        )
        def time_based_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action with simple time-based rate limiting.
            """
            # In a real implementation, this would call Facebook API
            return ProviderResponse(
                status="success",
                data={
                    "param": payload["param"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
        # Example 3: Action with no rate limiting
        @self.actions.register(
            name="unlimited_action",
            description="Action without rate limiting",
            payload_schema={
                "param": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            },
            rate_limit_monitor=NoRateLimitMonitor()
        )
        def unlimited_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action that can be called without any rate limits.
            """
            # In a real implementation, this would call Facebook API
            return ProviderResponse(
                status="success",
                data={
                    "param": payload["param"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            )
            
        # Example 4: Action with custom rate limit handling
        @self.actions.register(
            name="custom_rate_limit_action",
            description="Action with custom rate limit handling",
            payload_schema={
                "param": str
            },
            account_schema={
                "business_id": str,
                "access_token": str
            }
        )
        def custom_rate_limit_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action that implements custom rate limit handling.
            """
            # Check rate limits before processing
            limits = self.rate_limit_monitor.check_rate_limits()
            if limits and limits.get("rate_limited"):
                return ProviderResponse(
                    status="limit",
                    message=f"Rate limit exceeded. Please wait {limits['wait_time']} seconds",
                    data={"wait_time": limits["wait_time"]}
                )
                
            # Process the request
            result = {
                "param": payload["param"],
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            # Update rate limit after successful processing
            self.rate_limit_monitor.make_safe_request(lambda: None)
            
            return ProviderResponse(
                status="success",
                data=result
            )

if __name__ == "__main__":
    """
    Entry point for running the provider as a standalone service.
    """
    provider = RateLimitProvider()
    provider.start()