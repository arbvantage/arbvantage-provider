"""
Basic Provider Example

This example demonstrates the most basic usage of the Arbvantage Provider Framework with strict Pydantic validation.
It shows how to:
1. Create a simple provider
2. Register actions with Pydantic schemas
3. Handle strictly typed payloads
4. Return structured responses

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "basic-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
- TASK_EXECUTION_TIMEOUT: Timeout for task execution in seconds (defaults to 1)

Why is this important?
-----------------------------------
This example is a starting point for anyone new to the framework. It demonstrates
how to register actions, handle payloads, and return responses in a minimal and type-safe setup.
"""

import os
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from arbvantage_provider import Provider, ProviderResponse

# Define Pydantic schemas for payloads and accounts
class EchoPayload(BaseModel):
    message: str = Field(..., min_length=1, description="Message to echo back")

class AddNumbersPayload(BaseModel):
    a: float = Field(..., description="First number")
    b: float = Field(..., description="Second number")

class GreetPayload(BaseModel):
    name: str = Field(..., min_length=1, description="Name to greet")
    language: str = Field("en", description="Language code for greeting")

class ProfilePayload(BaseModel):
    username: str = Field(..., min_length=1, description="Username")
    profile: Dict[str, Any] = Field(..., description="Profile settings (nested dict)")
    tags: List[str] = Field(default_factory=list, description="List of tags")

class ProfileAccount(BaseModel):
    api_key: str = Field(..., min_length=32, description="API key for authentication")
    permissions: Dict[str, Any] = Field(..., description="Permissions (nested dict)")

class BasicProvider(Provider):
    """
    Basic provider example that implements simple echo and math operations with strict type validation.
    """
    def __init__(self):
        """
        Initialize the basic provider with environment variables and register actions with Pydantic schemas.
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "basic-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 1))
        )

        @self.actions.register(
            name="echo",
            description="Echo back the input message",
            payload_schema=EchoPayload
        )
        def echo(payload: EchoPayload) -> ProviderResponse:
            """
            Echo action that returns the input message.
            Args:
                payload (EchoPayload): Validated payload with a 'message' field.
            Returns:
                ProviderResponse: status 'success' and echoed message.
            """
            return ProviderResponse(
                status="success",
                data={"echo": payload.message}
            )

        @self.actions.register(
            name="add_numbers",
            description="Add two numbers together",
            payload_schema=AddNumbersPayload
        )
        def add_numbers(payload: AddNumbersPayload) -> ProviderResponse:
            """
            Add two numbers and return the result.
            Args:
                payload (AddNumbersPayload): Validated payload with 'a' and 'b'.
            Returns:
                ProviderResponse: status 'success' and the sum.
            """
            result = payload.a + payload.b
            return ProviderResponse(
                status="success",
                data={"sum": result}
            )

        @self.actions.register(
            name="greet",
            description="Generate a greeting message",
            payload_schema=GreetPayload
        )
        def greet(payload: GreetPayload) -> ProviderResponse:
            """
            Generate a greeting message in the specified language.
            Args:
                payload (GreetPayload): Validated payload with 'name' and optional 'language'.
            Returns:
                ProviderResponse: status 'success' and the greeting message.
            """
            greetings = {
                "en": "Hello",
                "es": "Hola",
                "fr": "Bonjour",
                "de": "Hallo"
            }
            greeting = greetings.get(payload.language, "Hello")
            return ProviderResponse(
                status="success",
                data={"message": f"{greeting}, {payload.name}!"}
            )

        @self.actions.register(
            name="create_profile",
            description="Create a user profile with nested settings and preferences",
            payload_schema=ProfilePayload,
            account_schema=ProfileAccount
        )
        def create_profile(payload: ProfilePayload, account: ProfileAccount) -> ProviderResponse:
            """
            Create a user profile with nested settings and preferences.
            Args:
                payload (ProfilePayload): Validated payload with username, profile, and tags.
                account (ProfileAccount): Validated account with api_key and permissions.
            Returns:
                ProviderResponse: status 'success' and the created profile data.
            """
            return ProviderResponse(
                status="success",
                data={
                    "username": payload.username,
                    "profile": payload.profile,
                    "tags": payload.tags,
                    "permissions": account.permissions
                }
            )

if __name__ == "__main__":
    """
    Run the provider if this script is executed directly.
    Example usage:
    1. Set environment variables:
       export PROVIDER_NAME="basic-provider"
       export PROVIDER_AUTH_TOKEN="your-auth-token"
       export HUB_GRPC_URL="hub-grpc:50051"
       export TASK_EXECUTION_TIMEOUT=1
    2. Run the provider:
       python basic_provider.py
    """
    provider = BasicProvider()
    provider.start() 