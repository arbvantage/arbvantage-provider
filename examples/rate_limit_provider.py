"""
Rate Limit Provider Example

This example demonstrates various approaches to rate limiting in providers using the Arbvantage Provider Framework and explicit Pydantic schemas.
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
from pydantic import BaseModel, Field
from arbvantage_provider import Provider, ProviderResponse
from arbvantage_provider.rate_limit import (
    RateLimitMonitor,
    TimeBasedRateLimitMonitor,
    AdvancedRateLimitMonitor
)
import time
import threading

# --- Pydantic Schemas ---
class GlobalLimitedActionPayload(BaseModel):
    param: str = Field(..., description="Some parameter")

class APIActionPayload(BaseModel):
    endpoint: str = Field(..., description="API endpoint")
    params: Dict[str, Any] = Field(..., description="Request parameters")

class CustomLimitedActionPayload(BaseModel):
    param: str = Field(..., description="Some parameter")

class CustomRateLimitMonitor(RateLimitMonitor):
    """
    Custom rate limit monitor implementation using a sliding window approach.
    This monitor is thread-safe and can be used for more granular rate limiting.
    """
    def __init__(self, max_requests: int = 100, window_size: int = 60):
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = []
        self.lock = threading.Lock()
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        with self.lock:
            self.requests = [t for t in self.requests if current_time - t < self.window_size]
            if len(self.requests) >= self.max_requests:
                wait_time = self.window_size - (current_time - self.requests[0])
                return {
                    "rate_limited": True,
                    "wait_time": wait_time,
                    "current_count": len(self.requests),
                    "limit": self.max_requests
                }
        return None
    def handle_throttling(self, wait_time: int = 60) -> None:
        time.sleep(wait_time)
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        limits = self.check_rate_limits()
        if limits and limits.get("rate_limited"):
            self.handle_throttling(limits["wait_time"])
        with self.lock:
            self.requests.append(time.time())
        return request_func(*args, **kwargs)

class RateLimitProvider(Provider):
    """
    Example provider demonstrating different rate limiting approaches using explicit Pydantic schemas.
    """
    def __init__(self):
        global_rate_limit = TimeBasedRateLimitMonitor(
            min_delay=1.0,
            max_calls_per_second=2,
            timezone="UTC"
        )
        super().__init__(
            name="rate-limit-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=global_rate_limit
        )
        self.api_rate_limit = AdvancedRateLimitMonitor(
            min_delay=0.5,
            max_calls_per_second=5,
            warning_threshold=0.8,
            critical_threshold=0.9
        )
        self.custom_rate_limit = CustomRateLimitMonitor(
            max_requests=50,
            window_size=60
        )
        self._register_actions()

    def _register_actions(self):
        @self.actions.register(
            name="global_limited_action",
            description="Action using global rate limit",
            payload_schema=GlobalLimitedActionPayload
        )
        def global_limited_action(payload: GlobalLimitedActionPayload) -> ProviderResponse:
            return ProviderResponse(
                status="success",
                data={"result": "global_limited", "param": payload.param}
            )

        @self.actions.register(
            name="api_action",
            description="Action with API-specific rate limit",
            payload_schema=APIActionPayload,
            rate_limit_monitor=self.api_rate_limit
        )
        def api_action(payload: APIActionPayload) -> ProviderResponse:
            limits = self.api_rate_limit.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.api_rate_limit.handle_throttling(limits["wait_time"])
            try:
                result = self._make_api_call(payload.endpoint, payload.params)
                return ProviderResponse(
                    status="success",
                    data={"status": "success", "data": result}
                )
            except Exception as e:
                return ProviderResponse(
                    status="error",
                    message=str(e)
                )

        @self.actions.register(
            name="custom_limited_action",
            description="Action with custom rate limit",
            payload_schema=CustomLimitedActionPayload,
            rate_limit_monitor=self.custom_rate_limit
        )
        def custom_limited_action(payload: CustomLimitedActionPayload) -> ProviderResponse:
            return ProviderResponse(
                status="success",
                data={"result": "custom_limited", "param": payload.param}
            )

    def _make_api_call(self, endpoint: str, params: dict) -> dict:
        time.sleep(0.1)
        return {"endpoint": endpoint, "params": params}

if __name__ == "__main__":
    provider = RateLimitProvider()
    provider.start() 