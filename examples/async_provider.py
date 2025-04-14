"""
Example of a provider with async operation support.

This example demonstrates how to implement async operations in a provider.
It shows:
- Async/await syntax usage
- Concurrent task execution
- Error handling in async context
- Rate limiting with async operations
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
                payload: Dictionary containing list of URLs
                
            Returns:
                ProviderResponse with fetched data
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
                payload: Dictionary containing URL and max retries
                
            Returns:
                ProviderResponse with fetched data
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
            url: URL to fetch
            
        Returns:
            Dictionary with response data
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
        """Cleanup resources."""
        if self.session:
            await self.session.close()
            
if __name__ == "__main__":
    provider = AsyncProvider()
    try:
        provider.start()
    finally:
        # Ensure cleanup
        asyncio.run(provider.cleanup()) 