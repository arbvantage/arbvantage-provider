"""
Rate Limit Provider Example

This example demonstrates various rate limiting strategies using the Arbvantage Provider Framework.
It shows how to:
1. Use different types of rate limit monitors
2. Configure rate limits at different levels
3. Handle rate limit responses
4. Implement custom rate limiting logic
"""

from arbvantage_provider import Provider
from arbvantage_provider.schemas import ProviderResponse
from arbvantage_provider.rate_limit import (
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor,
    NoRateLimitMonitor
)
import os
import time
from typing import Dict, Any

class RateLimitProvider(Provider):
    """
    Provider example demonstrating various rate limiting strategies.
    
    This provider shows different ways to implement rate limiting:
    - Global rate limits
    - Action-specific rate limits
    - Custom rate limit monitors
    - No rate limits
    """
    
    def __init__(self):
        """
        Initialize the rate limit provider with different rate limit configurations.
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "rate-limit-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Example 1: Action with no rate limits
        @self.actions.register(
            name="unlimited_action",
            description="Action without any rate limits",
            payload_schema={"message": str},
            rate_limit_monitor=NoRateLimitMonitor()  # Explicitly set no rate limits
        )
        def unlimited_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action that can be called without any rate limits.
            """
            return ProviderResponse(
                status="success",
                data={"message": payload["message"]}
            )
            
        # Example 2: Action with simple time-based rate limit
        @self.actions.register(
            name="slow_action",
            description="Action with 2-second delay between calls",
            payload_schema={"message": str},
            rate_limit_monitor=TimeBasedRateLimitMonitor(min_delay=2.0)
        )
        def slow_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action that can only be called once every 2 seconds.
            """
            return ProviderResponse(
                status="success",
                data={"message": payload["message"]}
            )
            
        # Example 3: Action with advanced rate limiting
        @self.actions.register(
            name="advanced_action",
            description="Action with advanced rate limiting (10 requests per minute)",
            payload_schema={"message": str},
            rate_limit_monitor=AdvancedRateLimitMonitor(
                requests_per_minute=10,
                burst_size=5
            )
        )
        def advanced_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action with sophisticated rate limiting using token bucket algorithm.
            Allows 10 requests per minute with bursts of up to 5 requests.
            """
            return ProviderResponse(
                status="success",
                data={"message": payload["message"]}
            )
            
        # Example 4: Action with custom rate limit handling
        @self.actions.register(
            name="custom_action",
            description="Action with custom rate limit handling",
            payload_schema={"message": str}
        )
        def custom_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action that implements custom rate limit handling.
            This example shows how to manually check and handle rate limits.
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
            result = {"message": payload["message"]}
            
            # Update rate limit after successful processing
            self.rate_limit_monitor.make_safe_request(lambda: None)
            
            return ProviderResponse(
                status="success",
                data=result
            )
            
        # Example 5: Action with conditional rate limiting
        @self.actions.register(
            name="conditional_action",
            description="Action with conditional rate limiting based on payload",
            payload_schema={
                "message": str,
                "priority": str  # "high" or "low"
            }
        )
        def conditional_action(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Action that applies different rate limits based on the priority.
            High priority requests bypass rate limits.
            """
            if payload["priority"] == "high":
                # High priority requests bypass rate limits
                return ProviderResponse(
                    status="success",
                    data={"message": payload["message"], "priority": "high"}
                )
            else:
                # Low priority requests use default rate limits
                limits = self.rate_limit_monitor.check_rate_limits()
                if limits and limits.get("rate_limited"):
                    return ProviderResponse(
                        status="limit",
                        message=f"Rate limit exceeded. Please wait {limits['wait_time']} seconds",
                        data={"wait_time": limits["wait_time"]}
                    )
                    
                self.rate_limit_monitor.make_safe_request(lambda: None)
                return ProviderResponse(
                    status="success",
                    data={"message": payload["message"], "priority": "low"}
                )

if __name__ == "__main__":
    """
    Run the rate limit provider if this script is executed directly.
    
    Example usage:
    1. Set environment variables:
       export PROVIDER_NAME="rate-limit-provider"
       export PROVIDER_AUTH_TOKEN="your-auth-token"
       export HUB_GRPC_URL="hub-grpc:50051"
       
    2. Run the provider:
       python rate_limit_provider.py
       
    The provider demonstrates different rate limiting strategies:
    - unlimited_action: No rate limits
    - slow_action: 2-second delay between calls
    - advanced_action: 10 requests per minute with burst of 5
    - custom_action: Manual rate limit handling
    - conditional_action: Priority-based rate limiting
    """
    provider = RateLimitProvider()
    provider.start() 