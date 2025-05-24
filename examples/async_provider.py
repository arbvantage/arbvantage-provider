"""
Async Provider Example

This example demonstrates how to implement a provider with async operation support using the Arbvantage Provider Framework.
It shows how to:
1. Use async/await syntax for concurrent HTTP requests
2. Register async actions
3. Handle rate limiting in async context
4. Clean up async resources

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "async-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")

Why is this important?
-----------------------------------
Async operations allow you to handle many concurrent I/O-bound tasks efficiently, which is critical for high-performance providers.
"""

import os
import asyncio
from typing import Dict, Any, List
import aiohttp
from arbvantage_provider import Provider, ProviderResponse
from arbvantage_provider.rate_limit import TimeBasedRateLimitMonitor

class AsyncProvider(Provider):
    """
    Provider with async operation support.
    
    This provider demonstrates how to implement async operations.
    It uses aiohttp for async HTTP requests and handles concurrent tasks.
    
    Why is this important?
    -----------------------------------
    Shows how to build scalable providers that can handle many concurrent requests.
    """
    
    def __init__(self):
        super().__init__(
            name="async-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Initialize rate limit monitor
        self.rate_limit_monitor = TimeBasedRateLimitMonitor(min_delay=0.5)
        
        # Initialize aiohttp session
        self.session = None
        
        # Register async actions
        self._register_async_actions()
        
    async def _init_session(self):
        """Initialize aiohttp session if not exists."""
        if self.session is None:
            self.session = aiohttp.ClientSession()
            
    def _register_async_actions(self):
        """Register async actions."""
        
        @self.actions.register(
            name="fetch_multiple_urls",
            description="Fetch multiple URLs concurrently",
            payload_schema={"urls": List[str]}
        )
        async def fetch_multiple_urls(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Fetch multiple URLs concurrently.
            
            Args:
                payload (dict): Must contain 'urls' as a list of URLs.
            Returns:
                ProviderResponse: status 'success' and fetched data.
            Why is this important?
            -----------------------------------
            Demonstrates concurrent I/O with async/await and error handling for each request.
            """
            urls = payload["urls"]
            
            # Initialize session if needed
            await self._init_session()
            
            # Create tasks for each URL
            tasks = [self._fetch_url(url) for url in urls]
            
            # Execute tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            successful = []
            failed = []
            
            for url, result in zip(urls, results):
                if isinstance(result, Exception):
                    failed.append({"url": url, "error": str(result)})
                else:
                    successful.append({"url": url, "data": result})
                    
            return ProviderResponse(
                status="success",
                message=f"Fetched {len(successful)} URLs, {len(failed)} failed",
                data={
                    "successful": successful,
                    "failed": failed
                }
            )
            
        @self.actions.register(
            name="fetch_with_retry",
            description="Fetch URL with retry logic",
            payload_schema={"url": str, "max_retries": int}
        )
        async def fetch_with_retry(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Fetch URL with retry logic.
            
            Args:
                payload (dict): Must contain 'url' and optionally 'max_retries'.
            Returns:
                ProviderResponse: status 'success' and fetched data, or 'error' on failure.
            Why is this important?
            -----------------------------------
            Shows how to implement retry logic and exponential backoff in async context.
            """
            url = payload["url"]
            max_retries = payload.get("max_retries", 3)
            
            # Initialize session if needed
            await self._init_session()
            
            for attempt in range(max_retries):
                try:
                    # Check rate limits
                    limits = self.rate_limit_monitor.check_rate_limits()
                    if limits and limits.get("rate_limited"):
                        await asyncio.sleep(limits["wait_time"])
                        
                    # Make request
                    async with self.session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()
                            return ProviderResponse(
                                status="success",
                                message=f"Successfully fetched URL on attempt {attempt + 1}",
                                data=data
                            )
                            
                    # If we get here, request failed
                    self.logger.warning(
                        "Request failed",
                        url=url,
                        attempt=attempt + 1,
                        status=response.status
                    )
                    
                except Exception as e:
                    self.logger.error(
                        "Request error",
                        url=url,
                        attempt=attempt + 1,
                        error=str(e)
                    )
                    
                # Wait before retry
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                
            return ProviderResponse(
                status="error",
                message=f"Failed to fetch URL after {max_retries} attempts",
                data={"url": url}
            )
            
    async def _fetch_url(self, url: str) -> Dict[str, Any]:
        """
        Fetch single URL with rate limiting.
        
        Args:
            url (str): URL to fetch
        Returns:
            dict: Response data
        Why is this important?
        -----------------------------------
        Shows how to combine rate limiting and async HTTP requests.
        """
        # Check rate limits
        limits = self.rate_limit_monitor.check_rate_limits()
        if limits and limits.get("rate_limited"):
            await asyncio.sleep(limits["wait_time"])
            
        # Make request
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"HTTP {response.status}")
                
    async def cleanup(self):
        """Cleanup resources (close aiohttp session)."""
        if self.session:
            await self.session.close()
            
if __name__ == "__main__":
    """
    Run the provider if this script is executed directly.
    
    Why is this important?
    -----------------------------------
    This allows you to test async actions and resource cleanup before integrating with the hub.
    """
    provider = AsyncProvider()
    try:
        provider.start()
    finally:
        # Ensure cleanup
        asyncio.run(provider.cleanup()) 