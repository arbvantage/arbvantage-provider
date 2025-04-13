"""
Basic Provider Example

This example demonstrates the most basic usage of the Arbvantage Provider Framework.
It shows how to:
1. Create a simple provider
2. Register basic actions
3. Handle simple payloads
4. Return responses
"""

from arbvantage_provider import Provider
from arbvantage_provider.schemas import ProviderResponse
import os
from typing import Dict, Any

class BasicProvider(Provider):
    """
    Basic provider example that implements simple echo and math operations.
    
    This provider demonstrates the fundamental features of the framework:
    - Basic action registration
    - Simple payload handling
    - Response formatting
    - Environment variable configuration
    """
    
    def __init__(self):
        """
        Initialize the basic provider with environment variables.
        
        The provider uses the following environment variables:
        - PROVIDER_NAME: Name of the provider (defaults to "basic-provider")
        - PROVIDER_AUTH_TOKEN: Authentication token for the hub
        - HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
        - TASK_EXECUTION_TIMEOUT: Timeout for task execution in seconds (defaults to 1)
        """
        super().__init__(
            name=os.getenv("PROVIDER_NAME", "basic-provider"),
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051"),
            execution_timeout=int(os.getenv("TASK_EXECUTION_TIMEOUT", 1))
        )
        
        # Register a simple echo action
        @self.actions.register(
            name="echo",
            description="Echo back the input message",
            payload_schema={
                "message": str  # Required string parameter
            }
        )
        def echo(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Simple echo action that returns the input message.
            
            Args:
                payload: Dictionary containing the input message
                
            Returns:
                Dictionary with the echoed message
            """
            return ProviderResponse(
                status="success",
                data={"echo": payload["message"]}
            )
            
        # Register a math operation action
        @self.actions.register(
            name="add_numbers",
            description="Add two numbers together",
            payload_schema={
                "a": float,  # First number
                "b": float   # Second number
            }
        )
        def add_numbers(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Add two numbers and return the result.
            
            Args:
                payload: Dictionary containing two numbers to add
                
            Returns:
                Dictionary with the sum of the numbers
            """
            result = payload["a"] + payload["b"]
            return ProviderResponse(
                status="success",
                data={"sum": result}
            )
            
        # Register an action with optional parameters
        @self.actions.register(
            name="greet",
            description="Generate a greeting message",
            payload_schema={
                "name": str,           # Required name parameter
                "language": str = None # Optional language parameter
            }
        )
        def greet(payload: Dict[str, Any]) -> Dict[str, Any]:
            """
            Generate a greeting message in the specified language.
            
            Args:
                payload: Dictionary containing name and optional language
                
            Returns:
                Dictionary with the greeting message
            """
            name = payload["name"]
            language = payload.get("language", "en")
            
            greetings = {
                "en": "Hello",
                "es": "Hola",
                "fr": "Bonjour",
                "de": "Hallo"
            }
            
            greeting = greetings.get(language, "Hello")
            return ProviderResponse(
                status="success",
                data={"message": f"{greeting}, {name}!"}
            )

if __name__ == "__main__":
    """
    Run the provider if this script is executed directly.
    
    Example usage:
    1. Set environment variables:
       export PROVIDER_NAME="basic-provider"
       export PROVIDER_AUTH_TOKEN="your-auth-token"
       export HUB_GRPC_URL="hub-grpc:50051"
       
    2. Run the provider:
       python basic_provider.py
    """
    provider = BasicProvider()
    provider.start() 