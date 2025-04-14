# Arbvantage Provider Framework

A comprehensive Python framework for building providers that communicate with the Arbvantage hub using gRPC. This framework abstracts away the complexity of gRPC communication, providing a clean and intuitive interface for implementing provider actions.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Detailed Usage](#detailed-usage)
- [Configuration](#configuration)
- [Action System](#action-system)
- [Error Handling](#error-handling)
- [Development Guide](#development-guide)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)
- [Rate Limiting](#rate-limiting)
- [Response Formats](#response-formats)
- [Advanced Features](#advanced-features)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Time Zone Support](#time-zone-support)
- [Logging and Monitoring](#logging-and-monitoring)
- [Security Considerations](#security-considerations)
- [Performance Optimization](#performance-optimization)
- [Testing and Debugging](#testing-and-debugging)

## Overview

The Arbvantage Provider Framework is designed to simplify the development of providers for the Arbvantage platform. It handles all the low-level gRPC communication details, allowing developers to focus on implementing business logic.

### Key Benefits
- **Simplified Development**: Focus on business logic instead of communication protocols
- **Automatic Connection Management**: Built-in retry mechanism and connection handling
- **Type Safety**: Comprehensive type hints for better development experience
- **Validation**: Built-in payload validation for actions
- **Scalability**: Designed for high-performance and scalable applications
- **Flexibility**: Support for various rate limiting strategies and monitoring options
- **Extensibility**: Easy to extend with custom implementations
- **Time Zone Support**: Built-in time zone handling for distributed systems
- **Comprehensive Logging**: Advanced logging capabilities with context
- **Security**: Built-in security features and best practices

## Features

### Core Features
- 🔄 Automatic connection handling with the Arbvantage hub
- 🔁 Built-in retry mechanism for failed connections
- 📝 Action registration system with payload validation
- 🛑 Graceful shutdown handling
- 📊 Comprehensive logging system
- 🎯 Type hints for better development experience
- 🔒 Secure authentication handling
- ⏱️ Configurable timeouts
- 🌍 Time zone support
- 📈 Performance monitoring

### Advanced Features
- 🚦 Sophisticated rate limiting system
- 🔄 Async operation support
- 💾 Built-in caching mechanisms
- 🔄 Retry logic with exponential backoff
- 📊 Custom monitoring capabilities
- 🔄 Distributed operation support
- 🔒 Advanced error handling
- 📝 Complex schema validation
- 🌐 Multi-timezone support
- 📊 Advanced metrics collection

## Installation

### Prerequisites
- Python 3.7 or higher
- pip (Python package manager)

### Installation Methods

#### Method 1: Install from GitHub
```bash
pip install git+https://github.com/arbvantage/arbvantage-provider.git
```

#### Method 2: Install from source
```bash
git clone https://github.com/arbvantage/arbvantage-provider.git
cd arbvantage-provider
pip install -e .
```

### Dependencies
The framework requires the following dependencies:
- grpcio
- grpcio-tools
- backoff
- protobuf
- pydantic
- requests
- pytz

## Quick Start

Here's a minimal example to get you started:

```python
from arbvantage_provider import Provider
import os

class MyProvider(Provider):
    def __init__(self):
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "my-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 1))
        )

        @self.actions.register(
            name="my_action",
            description="Description of what this action does",
            payload_schema={"param1": str, "param2": int}
        )
        def my_action(param1: str, param2: int):
            # Implementation of your action
            return {"result": "success"}

if __name__ == "__main__":
    provider = MyProvider()
    provider.start()
```

## Detailed Usage

### Provider Configuration

The Provider class accepts the following configuration parameters:

| Parameter | Type | Description | Default |
|-----------|------|-------------|---------|
| `name` | str | Unique identifier for your provider | Required |
| `auth_token` | str | Authentication token for the Arbvantage hub | Required |
| `hub_url` | str | URL of the Arbvantage hub | "hub-grpc:50051" |
| `execution_timeout` | int | Timeout for task execution in seconds | 1 |
| `rate_limit_monitor` | RateLimitMonitor | Custom rate limit monitor | None |
| `logger` | Logger | Custom logger instance | None |
| `timezone` | str | Timezone for the provider | "UTC" |

### Environment Variables

The framework supports configuration through environment variables:

```bash
export PROVIDER_NAME="my-provider"
export PROVIDER_AUTH_TOKEN="your-auth-token"
export HUB_GRPC_URL="hub-grpc:50051"
export TASK_EXECUTION_TIMEOUT=1
export PROVIDER_TIMEZONE="Europe/Moscow"
```

## Time Zone Support

The framework provides comprehensive time zone support for distributed systems. Here are some examples:

### Basic Time Zone Usage

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class TimeZoneProvider(Provider):
    def __init__(self):
        # Initialize with Moscow timezone
        super().__init__(
            name="timezone-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            timezone="Europe/Moscow"
        )
        
        # Rate limit monitor with timezone
        self.rate_limit_monitor = TimeBasedRateLimitMonitor(
            min_delay=1.0,
            timezone="Europe/Moscow"
        )
```

### Advanced Time Zone Features

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor
from datetime import datetime
import pytz

class AdvancedTimeZoneProvider(Provider):
    def __init__(self):
        # Initialize with multiple timezone support
        super().__init__(
            name="advanced-timezone-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            timezone="UTC"  # Default timezone
        )
        
        # Advanced rate limit monitor with timezone
        self.rate_limit_monitor = AdvancedRateLimitMonitor(
            min_delay=1.0,
            max_calls_per_second=2,
            warning_threshold=0.8,
            critical_threshold=0.9,
            timezone="Europe/Moscow"
        )
        
        # Register timezone-aware action
        @self.actions.register(
            name="timezone_action",
            description="Action with timezone awareness",
            payload_schema={"timezone": str}
        )
        def timezone_action(payload: dict) -> dict:
            # Get current time in specified timezone
            tz = pytz.timezone(payload["timezone"])
            current_time = datetime.now(tz)
            
            return {
                "status": "success",
                "data": {
                    "current_time": current_time.isoformat(),
                    "timezone": str(tz)
                }
            }
```

### Time Zone Best Practices

1. **Consistent Time Zone Usage**
   - Always specify timezone when creating providers
   - Use UTC for internal storage
   - Convert to local timezone only for display

2. **Rate Limiting with Time Zones**
   - Consider timezone differences in rate limiting
   - Use appropriate timezone for business hours
   - Handle daylight saving time changes

3. **Distributed Systems**
   - Use UTC for inter-service communication
   - Store timestamps with timezone information
   - Handle timezone conversions at the edge

## Action System

### Basic Action Registration

```python
@self.actions.register(
    name="action_name",
    description="Detailed description of the action",
    payload_schema={
        "param1": str,
        "param2": int,
        "optional_param": Optional[str]
    }
)
def action_handler(param1: str, param2: int, optional_param: Optional[str] = None):
    # Implementation
    return {"result": "success"}
```

### Complex Schema Validation

```python
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
        }
    }
)
def process_order(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Implementation
    return {"status": "success"}
```

### Async Operations

```python
@self.actions.register(
    name="async_action",
    description="Async action example",
    payload_schema={"param": str}
)
async def async_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Async implementation
    result = await some_async_operation(payload["param"])
    return {"result": result}
```

## Rate Limiting

### Basic Rate Limiting
```python
@self.actions.register(
    name="limited_action",
    description="Action with rate limiting",
    payload_schema={"param": str},
    rate_limit_monitor=TimeBasedRateLimitMonitor(
        min_delay=1.0,
        timezone="UTC"
    )
)
def limited_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": "success"}
```

### Advanced Rate Limiting
```python
@self.actions.register(
    name="advanced_action",
    description="Action with advanced rate limiting",
    payload_schema={"param": str},
    rate_limit_monitor=AdvancedRateLimitMonitor(
        requests_per_minute=60,
        burst_size=10,
        timezone="Europe/Moscow"
    )
)
def advanced_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    return {"result": "success"}
```

### Custom Rate Limit Monitor

```python
class CustomRateLimitMonitor(RateLimitMonitor):
    def __init__(self, max_requests: int = 100, window_size: int = 60, timezone: str = "UTC"):
        self.max_requests = max_requests
        self.window_size = window_size
        self.timezone = pytz.timezone(timezone)
        self.requests = []
        
    def _get_current_time(self) -> float:
        return datetime.now(self.timezone).timestamp()
        
    def check_rate_limits(self):
        current_time = self._get_current_time()
        self.requests = [t for t in self.requests 
                        if current_time - t < self.window_size]
        
        if len(self.requests) >= self.max_requests:
            return {
                "rate_limited": True,
                "wait_time": self.window_size - (current_time - self.requests[0]),
                "timezone": str(self.timezone)
            }
        return None
```

## Logging and Monitoring

### Basic Logging
```python
from arbvantage_provider.logger import Logger

class LoggingProvider(Provider):
    def __init__(self):
        # Initialize with custom logger
        logger = Logger(
            name="my-provider",
            level="INFO",
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        
        super().__init__(
            name="logging-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            logger=logger
        )
```

### Advanced Monitoring
```python
class MonitoredProvider(Provider):
    def __init__(self):
        super().__init__(
            name="monitored-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051"
        )
        
        # Custom monitoring setup
        self.metrics = {
            'requests': 0,
            'errors': 0,
            'avg_response_time': 0
        }
        
    def _process_task(self, task):
        start_time = time.time()
        try:
            result = super()._process_task(task)
            self._update_metrics(success=True, duration=time.time() - start_time)
            return result
        except Exception as e:
            self._update_metrics(success=False)
            raise
            
    def _update_metrics(self, success: bool, duration: float = 0):
        self.metrics['requests'] += 1
        if not success:
            self.metrics['errors'] += 1
        if duration > 0:
            self.metrics['avg_response_time'] = (
                (self.metrics['avg_response_time'] * (self.metrics['requests'] - 1) + duration)
                / self.metrics['requests']
            )
```

## Security Considerations

### Authentication
```python
class SecureProvider(Provider):
    def __init__(self):
        super().__init__(
            name="secure-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url="hub-grpc:50051"
        )
        
        # Additional security measures
        self._validate_auth_token()
        
    def _validate_auth_token(self):
        if not self.auth_token or len(self.auth_token) < 32:
            raise ValueError("Invalid authentication token")
```

### Input Validation
```python
@self.actions.register(
    name="secure_action",
    description="Action with input validation",
    payload_schema={
        "user_id": str,
        "action": str
    }
)
def secure_action(payload: Dict[str, Any]) -> Dict[str, Any]:
    # Validate input
    if not self._is_valid_user(payload["user_id"]):
        raise ValueError("Invalid user ID")
        
    if not self._is_allowed_action(payload["action"]):
        raise ValueError("Action not allowed")
        
    return {"status": "success"}
```

## Performance Optimization

### Caching
```python
from functools import lru_cache

class CachedProvider(Provider):
    @lru_cache(maxsize=100)
    def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        # Implementation
        return None
        
    @self.actions.register(
        name="cached_action",
        description="Action with caching",
        payload_schema={"key": str}
    )
    def cached_action(payload: Dict[str, Any]) -> Dict[str, Any]:
        cached_result = self._get_cached_data(payload["key"])
        if cached_result:
            return {"status": "success", "cached": True, "data": cached_result}
        # Implementation for non-cached case
```

### Async Operations
```python
class AsyncProvider(Provider):
    @self.actions.register(
        name="async_action",
        description="Async action example",
        payload_schema={"param": str}
    )
    async def async_action(payload: Dict[str, Any]) -> Dict[str, Any]:
        # Async implementation
        result = await self._process_async(payload["param"])
        return {"status": "success", "data": result}
```

## Testing and Debugging

### Unit Testing
```python
import unittest
from unittest.mock import Mock, patch

class TestProvider(unittest.TestCase):
    def setUp(self):
        self.provider = MyProvider()
        
    def test_action(self):
        result = self.provider.my_action("test", 123)
        self.assertEqual(result["status"], "success")
        
    @patch('arbvantage_provider.Provider._process_task')
    def test_rate_limiting(self, mock_process):
        # Test rate limiting
        pass
```

### Debugging
```python
class DebugProvider(Provider):
    def __init__(self):
        super().__init__(
            name="debug-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051"
        )
        
        # Enable debug logging
        self.logger.setLevel("DEBUG")
        
    def _process_task(self, task):
        self.logger.debug(f"Processing task: {task}")
        try:
            result = super()._process_task(task)
            self.logger.debug(f"Task result: {result}")
            return result
        except Exception as e:
            self.logger.error(f"Task failed: {str(e)}")
            raise
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please:
- Check the [documentation](https://github.com/arbvantage/arbvantage-provider/wiki)
- Open an [issue](https://github.com/arbvantage/arbvantage-provider/issues)
- Contact the maintainer at satsura@gmail.com

## Rate Limiting

The framework provides flexible rate limiting capabilities through the `RateLimitMonitor` interface. You can implement custom rate limiting logic or use built-in implementations.

### Built-in Rate Limit Monitors

#### 1. Time-Based Rate Limiting

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class MyProvider(Provider):
    def __init__(self):
        # Initialize with minimum delay of 2 seconds between requests
        rate_limit_monitor = TimeBasedRateLimitMonitor(min_delay=2.0)
        
        super().__init__(
            name="my-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=rate_limit_monitor
        )
```

#### 2. Advanced Rate Limiting with Token Bucket

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor

class MyProvider(Provider):
    def __init__(self):
        # Initialize with token bucket algorithm
        # 10 requests per minute, burst up to 20 requests
        rate_limit_monitor = AdvancedRateLimitMonitor(
            requests_per_minute=10,
            burst_size=20
        )
        
        super().__init__(
            name="my-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=rate_limit_monitor
        )
```

### Custom Rate Limit Implementation

You can create your own rate limiting implementation by extending the `RateLimitMonitor` class:

```python
from arbvantage_provider.rate_limit import RateLimitMonitor
import time
import redis
from typing import Dict, Any, Optional

class RedisRateLimitMonitor(RateLimitMonitor):
    """
    Rate limit monitor using Redis for distributed rate limiting
    """
    
    def __init__(self, redis_url: str, key_prefix: str = "rate_limit"):
        self.redis = redis.Redis.from_url(redis_url)
        self.key_prefix = key_prefix
        self.window_size = 60  # 1 minute window
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        current_time = int(time.time())
        window_key = f"{self.key_prefix}:{current_time // self.window_size}"
        
        # Get current request count
        count = self.redis.get(window_key)
        if count is None:
            count = 0
        else:
            count = int(count)
            
        # Check if we've exceeded the limit (e.g., 100 requests per minute)
        if count >= 100:
            return {
                "rate_limited": True,
                "wait_time": self.window_size - (current_time % self.window_size),
                "current_count": count,
                "limit": 100
            }
            
        return None
        
    def handle_throttling(self, wait_time: int = 60) -> None:
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        limits = self.check_rate_limits()
        if limits and limits.get("rate_limited"):
            self.handle_throttling(limits["wait_time"])
            
        # Increment request count
        current_time = int(time.time())
        window_key = f"{self.key_prefix}:{current_time // self.window_size}"
        self.redis.incr(window_key)
        self.redis.expire(window_key, self.window_size)
        
        return request_func(*args, **kwargs)

# Usage example
class MyProvider(Provider):
    def __init__(self):
        rate_limit_monitor = RedisRateLimitMonitor(
            redis_url="redis://localhost:6379/0",
            key_prefix="my_provider:rate_limit"
        )
        
        super().__init__(
            name="my-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=rate_limit_monitor
        )
```

### Rate Limit Monitoring in Actions

You can also implement rate limiting within specific actions:

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor
import time

class APIProvider(Provider):
    def __init__(self):
        # Global rate limit for all requests
        global_rate_limit = TimeBasedRateLimitMonitor(min_delay=1.0)
        
        super().__init__(
            name="api-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=global_rate_limit
        )
        
        # Action-specific rate limit
        self.api_rate_limit = TimeBasedRateLimitMonitor(min_delay=0.5)
        
        @self.actions.register(
            name="call_external_api",
            description="Call external API with rate limiting",
            payload_schema={
                "endpoint": str,
                "params": dict
            }
        )
        def call_external_api(payload: dict) -> dict:
            # Check action-specific rate limit
            limits = self.api_rate_limit.check_rate_limits()
            if limits and limits.get("rate_limited"):
                self.api_rate_limit.handle_throttling(limits["wait_time"])
                
            # Make API call
            try:
                # Your API call implementation here
                result = make_api_call(payload["endpoint"], payload["params"])
                
                # Update rate limit after successful call
                self.api_rate_limit.make_safe_request(lambda: None)
                
                return ProviderResponse(
                    status="success",
                    data=result
                )
            except Exception as e:
                return ProviderResponse(
                    status="error",
                    message=str(e)
                )
```

### Rate Limit Monitoring with Multiple Providers

For scenarios with multiple providers sharing the same rate limits:

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import RateLimitMonitor
import threading
import time

class SharedRateLimitMonitor(RateLimitMonitor):
    """
    Rate limit monitor shared between multiple providers
    """
    
    def __init__(self, max_requests: int = 100, window_size: int = 60):
        self.max_requests = max_requests
        self.window_size = window_size
        self.requests = []
        self.lock = threading.Lock()
        
    def check_rate_limits(self) -> Optional[Dict[str, Any]]:
        current_time = time.time()
        
        with self.lock:
            # Remove old requests
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
        time.sleep(wait_time)
        
    def make_safe_request(self, request_func: callable, *args, **kwargs) -> Any:
        limits = self.check_rate_limits()
        if limits and limits.get("rate_limited"):
            self.handle_throttling(limits["wait_time"])
            
        with self.lock:
            self.requests.append(time.time())
            
        return request_func(*args, **kwargs)

# Usage with multiple providers
shared_rate_limit = SharedRateLimitMonitor(max_requests=100, window_size=60)

class ProviderA(Provider):
    def __init__(self):
        super().__init__(
            name="provider-a",
            auth_token="token-a",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=shared_rate_limit
        )

class ProviderB(Provider):
    def __init__(self):
        super().__init__(
            name="provider-b",
            auth_token="token-b",
            hub_url="hub-grpc:50051",
            rate_limit_monitor=shared_rate_limit
        )
```

### Практические примеры использования Rate Limiting

#### 1. Глобальный rate limit как свойство класса

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class GlobalRateLimitProvider(Provider):
    # Определяем глобальный rate limit как свойство класса
    rate_limit_monitor = TimeBasedRateLimitMonitor(min_delay=1.0)
    
    def __init__(self):
        super().__init__(
            name="global-rate-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051"
        )
        
        # Все действия будут использовать глобальный rate limit
        @self.actions.register(
            name="action1",
            description="Действие с глобальным rate limit",
            payload_schema={"param": str}
        )
        def action1(payload: dict) -> dict:
            return {"result": "action1"}
            
        @self.actions.register(
            name="action2",
            description="Другое действие с тем же rate limit",
            payload_schema={"param": str}
        )
        def action2(payload: dict) -> dict:
            return {"result": "action2"}
```

#### 2. Rate limit для конкретного действия

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class PerActionRateLimitProvider(Provider):
    def __init__(self):
        super().__init__(
            name="per-action-rate-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051"
        )
        
        # Действие без rate limit
        @self.actions.register(
            name="unlimited_action",
            description="Действие без ограничений",
            payload_schema={"param": str}
        )
        def unlimited_action(payload: dict) -> dict:
            return {"result": "unlimited"}
            
        # Действие с быстрым rate limit
        @self.actions.register(
            name="fast_action",
            description="Действие с частыми запросами",
            payload_schema={"param": str},
            rate_limit_monitor=TimeBasedRateLimitMonitor(min_delay=0.1)  # Rate limit прямо в регистрации
        )
        def fast_action(payload: dict) -> dict:
            return {"result": "fast"}
            
        # Действие с медленным rate limit
        @self.actions.register(
            name="slow_action",
            description="Действие с редкими запросами",
            payload_schema={"param": str},
            rate_limit_monitor=TimeBasedRateLimitMonitor(min_delay=5.0)  # Rate limit прямо в регистрации
        )
        def slow_action(payload: dict) -> dict:
            return {"result": "slow"}
```

#### 3. Комбинированный подход

```python
from arbvantage_provider import Provider
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class CombinedRateLimitProvider(Provider):
    # Глобальный rate limit по умолчанию
    rate_limit_monitor = TimeBasedRateLimitMonitor(min_delay=1.0)
    
    def __init__(self):
        super().__init__(
            name="combined-rate-provider",
            auth_token="your-auth-token",
            hub_url="hub-grpc:50051"
        )
        
        # Действие с глобальным rate limit
        @self.actions.register(
            name="default_action",
            description="Действие с глобальным rate limit",
            payload_schema={"param": str}
        )
        def default_action(payload: dict) -> dict:
            return {"result": "default"}
            
        # Действие с собственным rate limit
        @self.actions.register(
            name="custom_action",
            description="Действие с собственным rate limit",
            payload_schema={"param": str},
            rate_limit_monitor=TimeBasedRateLimitMonitor(min_delay=0.5)  # Переопределяем глобальный limit
        )
        def custom_action(payload: dict) -> dict:
            return {"result": "custom"}
```

## Response Formats

The framework provides standardized response formats for all operations. Here are all possible response types:

### 1. Success Response
```python
{
    "status": "success",
    "data": {
        # Any data returned by the action
    }
}
```

### 2. Error Response
```python
{
    "status": "error",
    "message": "Error description",
    "data": {
        # Optional additional error data
    }
}
```

### 3. Rate Limit Response
```python
{
    "status": "limit",
    "message": "Rate limit exceeded. Please wait X seconds",
    "data": {
        "wait_time": 5.5,  # Time in seconds to wait before next request
        # Additional rate limit metrics depending on monitor type
    }
}
```

### 4. Validation Error Response
```python
{
    "status": "error",
    "message": "Invalid payload: Missing required parameters: param1, param2",
    "data": {
        "missing_params": ["param1", "param2"],
        "schema": {
            "param1": str,
            "param2": int
        }
    }
}
```

### 5. Authentication Error Response
```python
{
    "status": "error",
    "message": "Authentication failed: Invalid token",
    "data": {
        "error_code": "AUTH_ERROR",
        "details": "Token expired"
    }
}
```

### 6. Connection Error Response
```python
{
    "status": "error",
    "message": "Failed to connect to hub: Connection refused",
    "data": {
        "error_code": "CONNECTION_ERROR",
        "retry_count": 3,
        "next_retry": "2024-03-20T10:00:00Z"
    }
}
```

### 7. Action Not Found Response
```python
{
    "status": "error",
    "message": "Action 'unknown_action' not found",
    "data": {
        "available_actions": ["action1", "action2", "action3"]
    }
}
```

### 8. Advanced Rate Limit Response
```python
{
    "status": "limit",
    "message": "Rate limit exceeded. Please wait X seconds",
    "data": {
        "wait_time": 3.2,  # Time in seconds to wait before next request
        "metrics": {
            "call_count": 100,
            "total_time": 50.5,
            "total_cpu": 75.2
        },
        "is_near_limit": true,
        "is_critical": false,
        "call_usage": 0.85,
        "cpu_usage": 0.75
    }
}
```

### 9. Redis Rate Limit Response
```python
{
    "status": "limit",
    "message": "Rate limit exceeded. Please wait X seconds",
    "data": {
        "wait_time": 15.0,  # Time in seconds to wait before next request
        "current_count": 95,
        "limit": 100,
        "window_size": 60,
        "window_key": "rate_limit:1234567890"
    }
}
```

### 10. Shared Rate Limit Response
```python
{
    "status": "limit",
    "message": "Rate limit exceeded. Please wait X seconds",
    "data": {
        "wait_time": 10.0,  # Time in seconds to wait before next request
        "current_count": 98,
        "limit": 100,
        "window_size": 60,
        "providers": ["provider-a", "provider-b"]
    }
}
```

### Response Status Codes

The framework uses the following status codes:

| Status | Description | When Used |
|--------|-------------|-----------|
| `success` | Operation completed successfully | When action executes without errors |
| `error` | General error occurred | For validation, authentication, connection errors |
| `limit` | Rate limit exceeded | When rate limit is reached |

### Response Data Structure

All responses follow this basic structure:
```python
{
    "status": str,      # Status code (success/error/limit)
    "message": str,     # Human-readable message
    "data": dict       # Additional data (optional)
}
```

The `data` field is optional and its structure depends on the specific response type and context. For rate limit responses, the `wait_time` field indicates how many seconds you need to wait before making the next request. This value is always a positive number and represents the minimum time to wait to avoid rate limit restrictions.

## Examples

The framework comes with several example providers demonstrating different use cases:

### Basic Examples

1. **Basic Provider** (`examples/basic_provider.py`)
   - Simple provider implementation
   - Basic action registration
   - Error handling

2. **Rate Limit Provider** (`examples/rate_limit_provider.py`)
   - Rate limiting implementation
   - Different rate limit strategies
   - Monitoring and metrics

3. **Weather Provider** (`examples/weather_provider.py`)
   - External API integration
   - Data validation
   - Error handling

### Advanced Examples

1. **Redis Cached Provider** (`examples/redis_cached_provider.py`)
   - Redis caching implementation
   - Cache key generation
   - Cache invalidation
   - TTL management

2. **Async Provider** (`examples/async_provider.py`)
   - Async/await operations
   - Concurrent task execution
   - Error handling in async context
   - Rate limiting with async operations

3. **Database Provider** (`examples/database_provider.py`)
   - Database connection management
   - CRUD operations
   - Transaction handling
   - Error handling with database

4. **Message Queue Provider** (`examples/message_queue_provider.py`)
   - Message queue integration
   - Publishing messages
   - Consuming messages
   - Error handling with queues

5. **External API Provider** (`examples/external_api_provider.py`)
   - External API integration
   - API authentication
   - Rate limiting
   - Retry logic
   - Response caching

### Facebook Integration Example

The `examples/facebook/` directory contains a complete example of Facebook integration:

- **Facebook Provider** (`examples/facebook/facebook_provider.py`)
  - Facebook API integration
  - OAuth authentication
  - Graph API usage
  - Rate limiting
  - Error handling
