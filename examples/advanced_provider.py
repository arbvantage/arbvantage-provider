"""
Advanced Provider Example

This example demonstrates advanced features of the Arbvantage Provider Framework.
It shows how to:
1. Use complex payload and account schemas
2. Implement custom validation
3. Handle async operations
4. Use caching
5. Implement retry logic
6. Handle errors gracefully
7. Use custom monitoring
"""

from arbvantage_provider import Provider
from arbvantage_provider.schemas import ProviderResponse
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor
import os
import time
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache

class AdvancedProvider(Provider):
    """
    Advanced provider example demonstrating complex features.
    
    This provider shows advanced capabilities:
    - Complex schema validation
    - Async operations
    - Caching
    - Retry logic
    - Error handling
    - Custom monitoring
    """
    
    def __init__(self):
        """
        Initialize the advanced provider with complex configurations.
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "advanced-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Example 1: Complex schema validation
        @self.actions.register(
            name="process_order",
            description="Process a complex order with validation",
            payload_schema={
                "order_id": str,
                "items": [{
                    "product_id": str,
                    "quantity": int,
                    "price": float
                }],
                "customer": {
                    "name": str,
                    "email": str,
                    "address": {
                        "street": str,
                        "city": str,
                        "zip": str
                    }
                },
                "payment": {
                    "method": str,
                    "details": dict
                }
            },
            account_schema={
                "api_key": str,
                "merchant_id": str,
                "store_id": str
            }
        )
        def process_order(payload: Dict[str, Any], account: Dict[str, Any]) -> Dict[str, Any]:
            """
            Process an order with complex validation and error handling.
            """
            try:
                # Validate order total
                total = sum(item["quantity"] * item["price"] for item in payload["items"])
                if total <= 0:
                    return ProviderResponse(
                        status="error",
                        message="Invalid order total",
                        data={"error": "ORDER_TOTAL_INVALID"}
                    )
                
                # Process payment
                payment_result = self._process_payment(
                    payload["payment"],
                    account["api_key"]
                )
                
                if not payment_result["success"]:
                    return ProviderResponse(
                        status="error",
                        message="Payment processing failed",
                        data={"error": "PAYMENT_FAILED", "details": payment_result}
                    )
                
                # Create order record
                order_record = {
                    "order_id": payload["order_id"],
                    "total": total,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "merchant_id": account["merchant_id"],
                    "store_id": account["store_id"]
                }
                
                return ProviderResponse(
                    status="success",
                    data=order_record
                )
                
            except Exception as e:
                return ProviderResponse(
                    status="error",
                    message=str(e),
                    data={"error": "PROCESSING_ERROR"}
                )
        
        # Example 2: Async operation with caching
        @self.actions.register(
            name="get_weather_forecast",
            description="Get weather forecast with caching",
            payload_schema={
                "location": str,
                "days": int
            }
        )
        async def get_weather_forecast(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Get weather forecast with caching and async API calls.
            """
            cache_key = f"weather_{payload['location']}_{payload['days']}"
            cached_data = self._get_cached_forecast(cache_key)
            
            if cached_data:
                return ProviderResponse(
                    status="success",
                    data=cached_data,
                    metadata={"cached": True}
                )
            
            try:
                forecast = await self._fetch_weather_forecast(
                    payload["location"],
                    payload["days"]
                )
                
                self._cache_forecast(cache_key, forecast)
                
                return ProviderResponse(
                    status="success",
                    data=forecast,
                    metadata={"cached": False}
                )
                
            except Exception as e:
                return ProviderResponse(
                    status="error",
                    message="Failed to fetch weather data",
                    data={"error": str(e)}
                )
        
        # Example 3: Operation with retry logic
        @self.actions.register(
            name="process_payment",
            description="Process payment with retry logic",
            payload_schema={
                "amount": float,
                "currency": str,
                "payment_method": str,
                "retry_count": int
            },
            rate_limit_monitor=AdvancedRateLimitMonitor(
                requests_per_minute=60,
                burst_size=10
            )
        )
        def process_payment(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Process payment with automatic retry logic.
            """
            max_retries = payload.get("retry_count", 3)
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    result = self._process_payment_with_retry(
                        payload["amount"],
                        payload["currency"],
                        payload["payment_method"]
                    )
                    
                    return ProviderResponse(
                        status="success",
                        data=result,
                        metadata={"retry_count": retry_count}
                    )
                    
                except Exception as e:
                    retry_count += 1
                    if retry_count >= max_retries:
                        return ProviderResponse(
                            status="error",
                            message="Max retries exceeded",
                            data={"error": str(e), "retry_count": retry_count}
                        )
                    time.sleep(2 ** retry_count)  # Exponential backoff
        
        # Example 4: Deeply nested account schema
        @self.actions.register(
            name="deep_account_validation",
            description="Demonstrate deep validation of nested account schema",
            payload_schema={
                "operation": str
            },
            account_schema={
                "name": str,
                "settings": {
                    "api_key": str,
                    "advanced": {
                        "retry_count": int,
                        "proxy": {
                            "host": str,
                            "port": int
                        }
                    }
                }
            }
        )
        def deep_account_validation(payload: Dict[str, Any], account: Dict[str, Any]) -> ProviderResponse:
            """
            Demonstrate deep validation of nested account schema.

            Args:
                payload (dict): Must contain 'operation'.
                account (dict): Must contain 'name', 'settings' (with nested advanced and proxy).

            Returns:
                ProviderResponse: status 'success' and the validated account data.

            Why is this important?
            -----------------------------------
            Shows how the framework validates deeply nested account schemas and provides detailed error messages.
            """
            return ProviderResponse(
                status="success",
                data={
                    "operation": payload["operation"],
                    "account": account
                }
            )
    
    @lru_cache(maxsize=100)
    def _get_cached_forecast(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """
        Get cached weather forecast.
        """
        # Implementation would use a real cache system
        return None
    
    def _cache_forecast(self, cache_key: str, data: Dict[str, Any]) -> None:
        """
        Cache weather forecast data.
        """
        # Implementation would use a real cache system
        pass
    
    async def _fetch_weather_forecast(self, location: str, days: int) -> Dict[str, Any]:
        """
        Fetch weather forecast from external API.
        """
        # Simulate API call
        await asyncio.sleep(1)
        return {
            "location": location,
            "forecast": [
                {
                    "date": (datetime.now() + timedelta(days=i)).isoformat(),
                    "temperature": 20 + i,
                    "conditions": "sunny"
                }
                for i in range(days)
            ]
        }
    
    def _process_payment_with_retry(self, amount: float, currency: str, method: str) -> Dict[str, Any]:
        """
        Process payment with retry logic.
        """
        # Simulate payment processing
        if amount > 1000:
            raise Exception("Payment amount too high")
        return {
            "transaction_id": f"tx_{int(time.time())}",
            "amount": amount,
            "currency": currency,
            "status": "completed"
        }
    
    def _process_payment(self, payment: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """
        Process payment using payment provider.
        """
        # Simulate payment processing
        return {
            "success": True,
            "transaction_id": f"tx_{int(time.time())}",
            "status": "completed"
        }

if __name__ == "__main__":
    """
    Run the advanced provider if this script is executed directly.
    
    Example usage:
    1. Set environment variables:
       export PROVIDER_NAME="advanced-provider"
       export PROVIDER_AUTH_TOKEN="your-auth-token"
       export HUB_GRPC_URL="hub-grpc:50051"
       
    2. Run the provider:
       python advanced_provider.py
       
    The provider demonstrates advanced features:
    - Complex schema validation
    - Async operations
    - Caching
    - Retry logic
    - Error handling
    - Custom monitoring
    """
    provider = AdvancedProvider()
    provider.start() 