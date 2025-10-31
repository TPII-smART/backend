"""Redis client configuration."""
import redis.asyncio as redis
import json
import logging
import asyncio
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for caching Gemini API responses."""

    def __init__(self):
        """Initialize Redis connection config."""
        self._host = settings.REDIS_HOST
        self._port = settings.REDIS_PORT
        self._db = settings.REDIS_DB
        self._client_cache = {}

    def _get_client(self) -> redis.Redis:
        """Get or create Redis client for current event loop."""
        try:
            loop = asyncio.get_running_loop()
            loop_id = id(loop)
        except RuntimeError:
            # No event loop running, use a default client
            # This should only happen in synchronous contexts
            loop_id = 0
        
        if loop_id not in self._client_cache:
            self._client_cache[loop_id] = redis.Redis(
                host=self._host,
                port=self._port,
                db=self._db,
                decode_responses=True
            )
        return self._client_cache[loop_id]

    def get_client(self) -> redis.Redis:
        """Public method to get Redis client for testing purposes."""
        return self._get_client()

    async def get_cache(self, key: str) -> Optional[dict]:
        """
        Retrieve cached response from Redis.

        Args:
            key: Cache key (hash)

        Returns:
            Cached response dict or None
        """
        try:
            client = self._get_client()
            cached_data = await client.get(key)
            if cached_data:
                return json.loads(cached_data)
            return None
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None

    async def set_cache(self, key: str, value: dict, expire: int = 1):
        """
        Store response in Redis cache.

        Args:
            key: Cache key (hash)
            value: Response data to cache
            expire: Expiration time in seconds (default: 1 hour)
        """
        try:
            client = self._get_client()
            await client.setex(key, expire, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete_cache(self, key: str):
        """
        Delete cached response from Redis.

        Args:
            key: Cache key (hash)
        """
        try:
            client = self._get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")

    async def close_all(self):
        """Close all Redis connections."""
        for client in self._client_cache.values():
            await client.aclose()
        self._client_cache.clear()


# Global Redis client instance
redis_client = RedisClient()
