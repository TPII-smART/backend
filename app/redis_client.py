"""Redis client configuration."""
import redis
import json
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client for caching Gemini API responses."""

    def __init__(self):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )

    async def get_cache(self, key: str) -> Optional[dict]:
        """
        Retrieve cached response from Redis.

        Args:
            key: Cache key (hash)

        Returns:
            Cached response dict or None
        """
        try:
            cached_data = await self.client.get(key)
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
            await self.client.setex(key, expire, json.dumps(value))
        except Exception as e:
            logger.error(f"Redis set error: {e}")

    async def delete_cache(self, key: str):
        """
        Delete cached response from Redis.

        Args:
            key: Cache key (hash)
        """
        try:
            await self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}")


# Global Redis client instance
redis_client = RedisClient()
