"""
Advanced Provider Example

This example demonstrates advanced features of the Arbvantage Provider Framework using explicit Pydantic schemas.
It shows how to:
1. Use complex payload and account schemas
2. Implement custom validation
3. Handle async operations
4. Use caching
5. Implement retry logic
6. Handle errors gracefully
7. Use custom monitoring
"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from functools import lru_cache
from pydantic import BaseModel, Field
from arbvantage_provider import Provider, ProviderResponse
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor

# --- Pydantic Schemas ---

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity of product")
    price: float = Field(..., gt=0, description="Price per item")

class CustomerAddress(BaseModel):
    street: str
    city: str
    zip: str

class Customer(BaseModel):
    name: str
    email: str
    address: CustomerAddress

class PaymentInfo(BaseModel):
    method: str
    details: Dict[str, Any]

class ProcessOrderPayload(BaseModel):
    order_id: str
    items: List[OrderItem]
    customer: Customer
    payment: PaymentInfo

class ProcessOrderAccount(BaseModel):
    api_key: str
    merchant_id: str
    store_id: str

class WeatherForecastPayload(BaseModel):
    location: str
    days: int

class ProcessPaymentPayload(BaseModel):
    amount: float
    currency: str
    payment_method: str
    retry_count: int = 3

class DeepAccountAdvancedProxy(BaseModel):
    host: str
    port: int

class DeepAccountAdvanced(BaseModel):
    retry_count: int
    proxy: DeepAccountAdvancedProxy

class DeepAccountSettings(BaseModel):
    api_key: str
    advanced: DeepAccountAdvanced

class DeepAccount(BaseModel):
    name: str
    settings: DeepAccountSettings

class DeepAccountValidationPayload(BaseModel):
    operation: str

# --- Provider Implementation ---

class AdvancedProvider(Provider):
    """
    Advanced provider example demonstrating complex features with explicit Pydantic schemas.
    """
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "advanced-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )

        @self.actions.register(
            name="process_order",
            description="Process a complex order with validation",
            payload_schema=ProcessOrderPayload,
            account_schema=ProcessOrderAccount
        )
        def process_order(payload: ProcessOrderPayload, account: ProcessOrderAccount) -> ProviderResponse:
            try:
                total = sum(item.quantity * item.price for item in payload.items)
                if total <= 0:
                    return ProviderResponse(
                        status="error",
                        message="Invalid order total",
                        data={"error": "ORDER_TOTAL_INVALID"}
                    )
                payment_result = self._process_payment(payload.payment.model_dump(), account.api_key)
                if not payment_result["success"]:
                    return ProviderResponse(
                        status="error",
                        message="Payment processing failed",
                        data={"error": "PAYMENT_FAILED", "details": payment_result}
                    )
                order_record = {
                    "order_id": payload.order_id,
                    "total": total,
                    "status": "completed",
                    "timestamp": datetime.now().isoformat(),
                    "merchant_id": account.merchant_id,
                    "store_id": account.store_id
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

        @self.actions.register(
            name="get_weather_forecast",
            description="Get weather forecast with caching",
            payload_schema=WeatherForecastPayload
        )
        async def get_weather_forecast(payload: WeatherForecastPayload) -> ProviderResponse:
            cache_key = f"weather_{payload.location}_{payload.days}"
            cached_data = self._get_cached_forecast(cache_key)
            if cached_data:
                return ProviderResponse(
                    status="success",
                    data=cached_data,
                    metadata={"cached": True}
                )
            try:
                forecast = await self._fetch_weather_forecast(payload.location, payload.days)
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

        @self.actions.register(
            name="process_payment",
            description="Process payment with retry logic",
            payload_schema=ProcessPaymentPayload,
            rate_limit_monitor=AdvancedRateLimitMonitor(
                requests_per_minute=60,
                burst_size=10
            )
        )
        def process_payment(payload: ProcessPaymentPayload) -> ProviderResponse:
            max_retries = payload.retry_count
            retry_count = 0
            while retry_count < max_retries:
                try:
                    result = self._process_payment_with_retry(
                        payload.amount,
                        payload.currency,
                        payload.payment_method
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
                    time.sleep(2 ** retry_count)

        @self.actions.register(
            name="deep_account_validation",
            description="Demonstrate deep validation of nested account schema",
            payload_schema=DeepAccountValidationPayload,
            account_schema=DeepAccount
        )
        def deep_account_validation(payload: DeepAccountValidationPayload, account: DeepAccount) -> ProviderResponse:
            return ProviderResponse(
                status="success",
                data={
                    "operation": payload.operation,
                    "account": account.model_dump()
                }
            )

    @lru_cache(maxsize=100)
    def _get_cached_forecast(self, cache_key: str) -> Optional[Dict[str, Any]]:
        return None

    def _cache_forecast(self, cache_key: str, data: Dict[str, Any]) -> None:
        pass

    async def _fetch_weather_forecast(self, location: str, days: int) -> Dict[str, Any]:
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
        if amount > 1000:
            raise Exception("Payment amount too high")
        return {
            "transaction_id": f"tx_{int(time.time())}",
            "amount": amount,
            "currency": currency,
            "status": "completed"
        }

    def _process_payment(self, payment: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        return {
            "success": True,
            "transaction_id": f"tx_{int(time.time())}",
            "status": "completed"
        }

if __name__ == "__main__":
    provider = AdvancedProvider()
    provider.start() 