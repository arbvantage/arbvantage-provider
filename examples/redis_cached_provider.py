"""
Redis Cached Provider Example

This example demonstrates how to implement a provider with Redis caching support using the Arbvantage Provider Framework.
It shows how to:
1. Connect to a Redis instance
2. Cache API responses and manage TTL
3. Invalidate cache entries

Environment variables required:
- PROVIDER_NAME: Name of the provider (defaults to "redis-cached-provider")
- PROVIDER_AUTH_TOKEN: Authentication token for the hub
- HUB_GRPC_URL: URL of the hub service (defaults to "hub-grpc:50051")
- REDIS_HOST: Redis server host (defaults to "localhost")
- REDIS_PORT: Redis server port (defaults to 6379)
- REDIS_DB: Redis database number (defaults to 0)

Why is this important?
-----------------------------------
Caching is critical for performance and scalability. This example shows how to use Redis for caching in a provider.
"""

import os
import json
from typing import Dict, Any, Optional
import redis
from arbvantage_provider import Provider, ProviderResponse

class RedisCachedProvider(Provider):
    """
    Provider with Redis caching support.
    
    This provider demonstrates how to implement caching using Redis.
    It caches API responses and invalidates cache when needed.
    
    Why is this important?
    -----------------------------------
    Shows how to use external cache systems to improve performance and reduce load on APIs.
    """
    
    def __init__(self):
        super().__init__(
            name="redis-cached-provider",
            auth_token=os.getenv("PROVIDER_AUTH_TOKEN"),
            hub_url=os.getenv("HUB_GRPC_URL", "hub-grpc:50051")
        )
        
        # Initialize Redis connection
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            decode_responses=True
        )
        
        # Register cached actions
        self._register_cached_actions()
        
    def _register_cached_actions(self):
        """Register actions with caching support."""
        
        @self.actions.register(
            name="get_user_data",
            description="Get user data with caching",
            payload_schema={"user_id": str}
        )
        def get_user_data(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Get user data with Redis caching.
            
            Args:
                payload (dict): Must contain 'user_id'.
            Returns:
                ProviderResponse: status 'success' and user data, or 'error' on failure.
            Why is this important?
            -----------------------------------
            Shows how to implement read-through caching and TTL management.
            """
            user_id = payload["user_id"]
            cache_key = f"user:{user_id}"
            
            # Try to get from cache
            cached_data = self.redis_client.get(cache_key)
            if cached_data:
                self.logger.info("Cache hit", user_id=user_id)
                return ProviderResponse(
                    status="success",
                    message="Data retrieved from cache",
                    data=json.loads(cached_data)
                )
            
            # If not in cache, fetch from API
            self.logger.info("Cache miss", user_id=user_id)
            user_data = self._fetch_user_data(user_id)
            
            # Cache the result
            self.redis_client.setex(
                cache_key,
                3600,  # TTL in seconds (1 hour)
                json.dumps(user_data)
            )
            
            return ProviderResponse(
                status="success",
                message="Data retrieved from API",
                data=user_data
            )
            
        @self.actions.register(
            name="invalidate_user_cache",
            description="Invalidate user data cache",
            payload_schema={"user_id": str}
        )
        def invalidate_user_cache(payload: Dict[str, Any]) -> ProviderResponse:
            """
            Invalidate user data cache.
            
            Args:
                payload (dict): Must contain 'user_id'.
            Returns:
                ProviderResponse: status 'success' and invalidation result.
            Why is this important?
            -----------------------------------
            Shows how to explicitly invalidate cache entries when data changes.
            """
            user_id = payload["user_id"]
            cache_key = f"user:{user_id}"
            
            # Delete from cache
            deleted = self.redis_client.delete(cache_key)
            
            return ProviderResponse(
                status="success",
                message="Cache invalidated" if deleted else "No cache entry found",
                data={"user_id": user_id, "deleted": bool(deleted)}
            )
            
    def _fetch_user_data(self, user_id: str) -> Dict[str, Any]:
        """
        Simulate fetching user data from an API.
        
        Args:
            user_id (str): User identifier
        Returns:
            dict: User data
        Why is this important?
        -----------------------------------
        In a real provider, this would call an external API or database. Here, it simulates a data source.
        """
        # In a real implementation, this would make an API call
        return {
            "id": user_id,
            "name": f"User {user_id}",
            "email": f"user{user_id}@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }

if __name__ == "__main__":
    """
    Run the provider if this script is executed directly.
    
    Why is this important?
    -----------------------------------
    This allows you to test caching logic before integrating with the hub.
    """
    provider = RedisCachedProvider()
    provider.start() 