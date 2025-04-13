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

## Overview

The Arbvantage Provider Framework is designed to simplify the development of providers for the Arbvantage platform. It handles all the low-level gRPC communication details, allowing developers to focus on implementing business logic.

### Key Benefits
- **Simplified Development**: Focus on business logic instead of communication protocols
- **Automatic Connection Management**: Built-in retry mechanism and connection handling
- **Type Safety**: Comprehensive type hints for better development experience
- **Validation**: Built-in payload validation for actions
- **Scalability**: Designed for high-performance and scalable applications

## Features

- 🔄 Automatic connection handling with the Arbvantage hub
- 🔁 Built-in retry mechanism for failed connections
- 📝 Action registration system with payload validation
- 🛑 Graceful shutdown handling
- 📊 Comprehensive logging system
- 🎯 Type hints for better development experience
- 🔒 Secure authentication handling
- ⏱️ Configurable timeouts

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

### Environment Variables

The framework supports configuration through environment variables:

```bash
export PROVIDER_NAME="my-provider"
export PROVIDER_AUTH_TOKEN="your-auth-token"
export HUB_GRPC_URL="hub-grpc:50051"
export TASK_EXECUTION_TIMEOUT=1
```

## Action System

### Registering Actions

Actions are registered using the `@actions.register` decorator:

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

### Payload Validation

The framework automatically validates incoming payloads against the defined schema:

```python
payload_schema = {
    "required_string": str,
    "required_int": int,
    "optional_float": Optional[float],
    "nested": {
        "field": str
    }
}
```

### Complex Nested Structures

The framework supports complex nested structures with multiple levels of nesting. Here's an example of a complex schema for a user management system:

```python
from typing import List, Optional, Dict, Any
from datetime import datetime

@self.actions.register(
    name="create_user",
    description="Create a new user with complex profile data",
    payload_schema={
        "user": {
            "personal_info": {
                "first_name": str,
                "last_name": str,
                "date_of_birth": datetime,
                "gender": str,
                "nationality": str
            },
            "contact_info": {
                "email": str,
                "phone": str,
                "addresses": List[Dict[str, str]],  # List of address dictionaries
                "emergency_contacts": List[{
                    "name": str,
                    "relationship": str,
                    "phone": str
                }]
            },
            "preferences": {
                "language": str,
                "timezone": str,
                "notifications": {
                    "email": bool,
                    "sms": bool,
                    "push": bool
                },
                "privacy_settings": {
                    "profile_visibility": str,
                    "data_sharing": bool
                }
            },
            "subscriptions": List[{
                "service": str,
                "plan": str,
                "start_date": datetime,
                "end_date": Optional[datetime],
                "features": List[str]
            }]
        },
        "metadata": {
            "source": str,
            "created_by": str,
            "tags": List[str],
            "custom_fields": Dict[str, Any]  # Flexible dictionary for additional data
        }
    }
)
def create_user(payload: Dict) -> Dict:
    """
    Create a new user with complex profile data
    
    Args:
        payload: Dictionary containing user data with nested structures
        
    Returns:
        Dict: Response with created user information
    """
    try:
        # Process the complex nested data
        user_data = payload["user"]
        
        # Example of accessing nested data
        personal_info = user_data["personal_info"]
        contact_info = user_data["contact_info"]
        preferences = user_data["preferences"]
        
        # Process addresses
        addresses = contact_info["addresses"]
        for address in addresses:
            # Process each address
            pass
            
        # Process emergency contacts
        emergency_contacts = contact_info["emergency_contacts"]
        for contact in emergency_contacts:
            # Process each emergency contact
            pass
            
        # Process subscriptions
        subscriptions = user_data["subscriptions"]
        for subscription in subscriptions:
            # Process each subscription
            pass
            
        return ProviderResponse(
            status="success",
            message="User created successfully",
            data={
                "user_id": "generated_id",
                "created_at": datetime.now().isoformat(),
                "profile_summary": {
                    "name": f"{personal_info['first_name']} {personal_info['last_name']}",
                    "email": contact_info["email"],
                    "subscriptions_count": len(subscriptions)
                }
            }
        )
        
    except Exception as e:
        return ProviderResponse(
            status="error",
            message=f"Failed to create user: {str(e)}"
        )
```

This example demonstrates:
- Multiple levels of nesting
- Lists of dictionaries
- Optional fields
- Complex data types (datetime)
- Flexible data structures (Dict[str, Any])
- Nested validation
- Error handling for complex structures

## Error Handling

The framework provides several custom exceptions:

- `ActionNotFoundError`: Raised when an undefined action is requested
- `InvalidPayloadError`: Raised when the payload doesn't match the schema
- `ConnectionError`: Raised when there are issues connecting to the hub
- `AuthenticationError`: Raised when authentication fails

Example error handling:

```python
try:
    provider.start()
except ConnectionError as e:
    print(f"Failed to connect to hub: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
```

## Development Guide

### Setting Up Development Environment

1. Clone the repository:
```bash
git clone https://github.com/arbvantage/arbvantage-provider.git
cd arbvantage-provider
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/MacOS
# or
venv\Scripts\activate  # Windows
```

3. Install development dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

### Running Tests

```bash
python -m pytest tests/
```

## Project Structure

```
arbvantage_provider/
├── __init__.py          # Package initialization
├── actions.py           # Action registration and management
├── exceptions.py        # Custom exceptions
├── provider.py          # Main Provider class
└── protos/             # Protocol Buffer definitions
    └── hub.proto       # Proto file for hub communication
```

## API Reference

### Provider Class

```python
class Provider:
    def __init__(
        self,
        name: str,
        auth_token: str,
        hub_url: str = "hub-grpc:50051",
        execution_timeout: int = 1
    ):
        pass

    def start(self) -> None:
        """Start the provider and establish connection with the hub."""
        pass

    def stop(self) -> None:
        """Stop the provider and close the connection."""
        pass
```

### Actions Registry

```python
class Actions:
    def register(
        self,
        name: str,
        description: str,
        payload_schema: Dict[str, Any]
    ) -> Callable:
        """Register a new action with the provider."""
        pass
```

## Examples

### Basic Provider

```python
from arbvantage_provider import Provider
import os

class BasicProvider(Provider):
    def __init__(self):
        super().__init__(
            name="basic-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )

        @self.actions.register(
            name="echo",
            description="Echo back the input",
            payload_schema={"message": str}
        )
        def echo(message: str):
            return {"echo": message}

if __name__ == "__main__":
    provider = BasicProvider()
    provider.start()
```

### Advanced Provider with Error Handling

```python
from arbvantage_provider import Provider, ActionNotFoundError, InvalidPayloadError
import os

class AdvancedProvider(Provider):
    def __init__(self):
        super().__init__(
            name="advanced-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN")
        )

        @self.actions.register(
            name="process_data",
            description="Process input data",
            payload_schema={
                "data": list,
                "options": dict
            }
        )
        def process_data(data: list, options: dict):
            try:
                # Process data
                return {"status": "success", "processed": len(data)}
            except Exception as e:
                return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    try:
        provider = AdvancedProvider()
        provider.start()
    except Exception as e:
        print(f"Provider failed to start: {e}")
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

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
