from typing import List, Optional, Union

import redis
from django.conf import settings


class RedisClient:
    """A simple synchronous Redis client wrapper for working with configured Django cache stores."""

    def __init__(self, cache_name: str = "default") -> None:
        """Initializes a Redis client for the specified cache store."""
        cache_settings = settings.CACHES.get(cache_name)
        if not cache_settings:
            raise ValueError(
                f'Cache store with the name "{cache_name}" not found in CACHES settings.'
            )

        # Explicitly use a synchronous Redis client
        self.client: redis.Redis = redis.Redis.from_url(
            cache_settings["LOCATION"]
        )

    def get(self, key: str) -> Optional[str]:
        """Retrieves a value from Redis by key."""
        value = self.client.get(key)
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return None

    def set(
        self,
        key: str,
        value: Union[str, bytes, int, float],
        expires: Optional[int] = None,
    ) -> bool:
        """Sets a key-value pair in Redis with an optional expiration time."""
        result = self.client.set(key, value, ex=expires)
        return bool(result)

    def delete(self, key: str) -> int:
        """Deletes a key from Redis and returns the number of deleted keys."""
        result = self.client.delete(key)
        if isinstance(result, (int, float)):
            return int(result)
        return 0

    def update(self, key: str, value: Union[str, bytes, int, float]) -> bool:
        """Updates a key in Redis without resetting its expiration time."""
        ttl = self.client.ttl(key)
        if isinstance(ttl, int) and ttl > 0:
            result = self.client.set(key, value, ex=ttl)
            return bool(result)
        elif ttl == -1:
            # If TTL is -1, the key has no expiration — update without ex
            result = self.client.set(key, value)
            return bool(result)
        return False

    def keys(self, pattern: str) -> List[str]:
        """Returns all keys matching a given pattern."""
        keys = self.client.keys(pattern)
        if not isinstance(keys, list):
            raise TypeError("Expected Redis keys() to return a list of bytes.")
        return [key.decode("utf-8") for key in keys]
