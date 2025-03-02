# Arbvantage Provider

A Python framework for creating providers that can communicate with the Arbvantage hub using gRPC. This framework simplifies the process of creating scalable and reliable providers by handling the communication layer and providing a clean interface for implementing provider actions.

## Description

Arbvantage Provider is a framework designed to simplify the process of creating providers for the Arbvantage platform. It provides:

- Automatic connection handling with the Arbvantage hub
- Built-in retry mechanism for failed connections
- Action registration system with payload validation
- Graceful shutdown handling
- Logging system
- Type hints for better development experience

## Requirements

- Python 3.7 or higher
- pip (Python package manager)

## Installation

Install directly from GitHub:

```bash
pip install git+https://github.com/arbvantage/arbvantage-provider.git
```

Or install from source:

```bash
git clone https://github.com/arbvantage/arbvantage-provider.git
cd arbvantage-provider
pip install -e .
```

## Dependencies

Main project dependencies:
- grpcio >= 1.44.0 - gRPC framework
- backoff >= 2.1.2 - For implementing retry mechanism
- protobuf >= 3.20.0 - Protocol Buffers
- grpcio-tools >= 1.44.0 - Tools for working with gRPC

## Usage

### Basic Provider Implementation

Here's a basic example of how to create a provider:

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

        # Register provider actions
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

### Provider Configuration

The Provider class accepts the following parameters:

- `name` (str): Unique identifier for your provider
- `auth_token` (str): Authentication token for the Arbvantage hub
- `hub_url` (str): URL of the Arbvantage hub (default: "hub-grpc:50051")
- `execution_timeout` (int): Timeout for task execution in seconds (default: 1)

### Action Registration

Actions are registered using the `@actions.register` decorator with the following parameters:

- `name` (str): Name of the action
- `description` (str): Description of what the action does
- `payload_schema` (dict): Schema for validating incoming payloads

### Error Handling

The framework provides custom exceptions for common error cases:

- `ActionNotFoundError`: Raised when an undefined action is requested
- `InvalidPayloadError`: Raised when the payload doesn't match the schema

## Development

To set up the development environment:

1. Clone the repository:
```bash
git clone https://github.com/arbvantage/arbvantage-provider.git
cd arbvantage-provider
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # for Linux/MacOS
# or
venv\Scripts\activate  # for Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install the package in development mode:
```bash
pip install -e .
```

## Project Structure

```
arbvantage_provider/
├── __init__.py          # Package initialization
├── actions.py           # Action registration and management
├── exceptions.py        # Custom exceptions
├── provider.py          # Main Provider class
├── hub_pb2.py          # Generated Protocol Buffers
├── hub_pb2_grpc.py     # Generated gRPC code
└── protos/             # Protocol Buffer definitions
```

## License

MIT License

## Author

Valera Satsura (satsura@gmail.com)

## Support

If you encounter any problems or have questions, please create an issue in the project repository: https://github.com/arbvantage/arbvantage-provider
