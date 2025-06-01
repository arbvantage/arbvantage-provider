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
- [Writing Actions](#writing-actions)
- [Nested Schema Validation](#nested-schema-validation)

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

## Overview

The rate limiting system provides flexible and configurable rate limiting functionality for API requests. It supports multiple strategies and can be easily extended.

## Types of Rate Limiting

### 1. No Rate Limiting
Pass-through implementation that allows all requests without any restrictions.

```python
from arbvantage_provider.rate_limit import NoRateLimitMonitor

# Default monitor for new providers
provider = Provider(
    name="my-provider",
    auth_token="my-token",
    hub_url="hub-grpc:50051"
)

# Explicitly set no rate limiting
provider = Provider(
    name="my-provider",
    auth_token="my-token",
    hub_url="hub-grpc:50051",
    rate_limit_monitor=NoRateLimitMonitor()
)

# For specific actions
@provider.actions.register(
    name="unlimited_action",
    description="Action without rate limits",
    payload_schema={"param": str},
    rate_limit_monitor=NoRateLimitMonitor()
)
def unlimited_action(param: str) -> dict:
    return {"result": "success"}
```

### 2. Time-Based Rate Limiting
Simple time-based approach that ensures minimum delay between requests.

```python
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

monitor = TimeBasedRateLimitMonitor(
    min_delay=1.0,  # Minimum delay between requests in seconds
    max_calls_per_second=1  # Maximum number of calls per second
)
```

### 3. Advanced Rate Limiting
Includes warning and critical thresholds with logging.

```python
from arbvantage_provider.rate_limit import AdvancedRateLimitMonitor

monitor = AdvancedRateLimitMonitor(
    min_delay=0.5,
    max_calls_per_second=2,
    warning_threshold=0.8,  # 80% of limit
    critical_threshold=0.9  # 90% of limit
)
```

### 4. Custom Rate Limiting
Sliding window approach for more granular control.

```python
from arbvantage_provider.rate_limit import CustomRateLimitMonitor

monitor = CustomRateLimitMonitor(
    window_size=60,  # Window size in seconds
    max_requests=100  # Maximum requests per window
)
```

## Using Rate Limit Provider

### Basic Usage

```python
from arbvantage_provider.rate_limit_provider import RateLimitProvider

# Create provider with no rate limiting (default)
provider = RateLimitProvider()

# Create provider with time-based rate limiting
provider = RateLimitProvider(
    monitor_class=TimeBasedRateLimitMonitor,
    min_delay=1.0,
    max_calls_per_second=1
)

# Make a request
result = provider.make_safe_request(my_api_call, arg1, arg2)
```

### API-Specific Rate Limiting

```python
class FacebookProvider(RateLimitProvider):
    def __init__(self):
        super().__init__(
            monitor_class=AdvancedRateLimitMonitor,
            min_delay=0.5,
            max_calls_per_second=2,
            warning_threshold=0.8,
            critical_threshold=0.9
        )
```

### Custom Rate Limiting

```python
class CustomProvider(RateLimitProvider):
    def __init__(self):
        super().__init__(
            monitor_class=CustomRateLimitMonitor,
            window_size=60,
            max_requests=100
        )
```

## Response Format

When rate limits are exceeded, the system returns a dictionary with the following information:

```python
{
    "error": "Rate limit exceeded",
    "retry_after": 5.0,  # Seconds to wait before retrying
    "current_usage": 0.9,  # Current usage ratio (0.0 to 1.0)
    "limit_type": "time_based"  # Type of rate limit
}
```

## Best Practices

1. **Choose Appropriate Strategy**
   - Use NoRateLimitMonitor when no limits are needed
   - Use time-based for simple APIs
   - Use advanced for APIs with strict limits
   - Use custom for complex rate limiting needs

2. **Monitor Usage**
   - Check rate limits before making requests
   - Handle rate limit responses gracefully
   - Log warnings and critical states

3. **Configuration**
   - Set realistic limits based on API requirements
   - Adjust thresholds based on usage patterns
   - Update configuration as needed

4. **Error Handling**
   - Implement retry logic for rate limit errors
   - Use exponential backoff for retries
   - Log rate limit violations

## Implementation Details

The rate limiting system is implemented using:

- Thread-safe operations with `threading.Lock`
- Flexible monitoring strategies
- Configurable thresholds and limits
- Detailed logging and error reporting
- Zero-overhead pass-through when no limits are needed

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

## Writing Actions

You can write actions with any signature you want. The framework will automatically filter parameters
and only pass those that your handler accepts. This gives you maximum flexibility and safety.

### Example 1: Minimal action (no parameters)

```python
@self.actions.register(
    name="ping",
    description="Simple ping action"
)
def ping():
    # This action does not require any parameters
    return {"result": "pong"}
```

### Example 2: Action with explicit parameters

```python
@self.actions.register(
    name="echo",
    description="Echoes the payload",
    payload_schema={"message": str}
)
def echo(payload, logger):
    # 'payload' and 'logger' will be passed automatically
    logger.info(f"Payload: {payload}")
    return {"result": payload["message"]}
```

### Example 3: Action with **kwargs for extra flexibility

```python
@self.actions.register(
    name="flexible_action",
    description="Accepts any parameters"
)
def flexible_action(payload, **kwargs):
    # 'payload' is required, all other parameters (logger, provider, account, etc.)
    # will be available in kwargs if needed
    logger = kwargs.get("logger")
    if logger:
        logger.info(f"Payload: {payload}")
    return {"received": payload}
```

### Example 4: Action with only **kwargs

```python
@self.actions.register(
    name="catch_all",
    description="Catches all parameters"
)
def catch_all(**kwargs):
    # All parameters (payload, account, provider, logger, etc.) will be in kwargs
    return {"all_params": kwargs}
```

### How it works

- The framework uses Python's inspect module to analyze your action's signature.
- Only the parameters that your handler accepts will be passed.
- If you use **kwargs, you can access any extra parameters you need.
- This approach allows you to write both strict and flexible actions, depending on your needs.

## Nested Schema Validation

The framework now supports deep (recursive) validation of nested dictionaries and lists in both `payload_schema` and `account_schema`. This means you can define complex, deeply nested structures for your action schemas, and the framework will automatically validate incoming data against these schemas.

### Example: Nested Payload Schema

```python
@self.actions.register(
    name="create_user_profile",
    description="Create a user profile with nested settings and preferences",
    payload_schema={
        "username": str,
        "profile": {
            "first_name": str,
            "last_name": str,
            "settings": {
                "theme": str,
                "notifications": {
                    "email": bool,
                    "sms": bool
                }
            }
        },
        "tags": [str]  # List of strings
    },
    account_schema={
        "api_key": str,
        "permissions": {
            "admin": bool,
            "scopes": [str]
        }
    }
)
def create_user_profile(payload: dict, account: dict):
    # Implementation
    return {"status": "success"}
```

### How Validation Works
- **Missing keys**: If any required key (even deeply nested) is missing, a detailed error will be returned with the full path to the missing key.
- **Type mismatches**: If a value does not match the expected type (including inside lists or nested dicts), a detailed error will be returned.
- **Lists**: You can specify lists of types or lists of dicts, and each item will be validated.

### Example Error Output
If the payload is missing `profile.settings.notifications.sms`, the error will look like:

```json
{
  "status": "error",
  "message": "Payload validation failed",
  "data": {
    "errors": [
      "Missing key: profile.settings.notifications.sms"
    ]
  }
}
```

### Best Practices
- Always define your schemas as deeply as your business logic requires.
- Use lists and nested dicts to express complex data structures.
- The validation system will help you catch errors early and provide clear feedback to API users.

---
