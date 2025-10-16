import hashlib
import json
from functools import wraps
from typing import Any, Callable, Optional
from urllib.parse import urlencode

from rest_framework.response import Response

from utils.redis_client import RedisClient


def generate_cache_key(
    prefix: str,
    slug: Optional[str] = None,
    query_params: Optional[dict] = None,
) -> str:
    """Generates a cache key based on a prefix, slug, and query parameters."""
    base_key = f"{prefix}:{slug}" if slug else prefix
    if query_params:
        sorted_params = urlencode(sorted(query_params.items()))
        hashed_params = hashlib.md5(sorted_params.encode()).hexdigest()
        return f"{base_key}:{hashed_params}"
    return base_key


def clear_cache_by_prefix(prefix: str) -> None:
    """Deletes all cache keys that start with the given prefix."""
    redis_client = RedisClient("cache")
    keys = redis_client.keys(f"{prefix}*")
    if keys:
        for key in keys:  # Delete keys one by one
            redis_client.delete(key)


def cache_response(
    prefix: str,
    timeout: int = 60 * 60 * 24,
    cache_key_func: Optional[Callable[[str, dict, dict], str]] = None,
) -> Callable:
    """Decorator that caches JSON responses using RedisClient."""

    def decorator(func: Callable) -> Callable:
        """Wraps a view function to add caching logic."""

        @wraps(func)
        def wrapper(
            self: Any, request: Any, *args: Any, **kwargs: Any
        ) -> Response:
            """Returns a cached response if present, otherwise executes the view and caches the result."""
            redis_client = RedisClient("cache")

            # Generate cache key
            if cache_key_func:
                cache_key = cache_key_func(prefix, request.GET.dict(), kwargs)
            else:
                query_params = urlencode(sorted(request.GET.items()))
                hashed_params = hashlib.md5(query_params.encode()).hexdigest()
                slug = kwargs.get("slug", "")
                cache_key = f"{prefix}:{slug}:{hashed_params}"

            # Check cache
            cached_data = redis_client.get(cache_key)
            if cached_data is not None:
                # Load data from cache and return as a Response
                return Response(json.loads(cached_data))

            # Execute the original function
            response = func(self, request, *args, **kwargs)

            # Save response data to cache if it is a Response instance
            if isinstance(response, Response):
                redis_client.set(
                    cache_key, json.dumps(response.data), expires=timeout
                )

            return response

        return wrapper

    return decorator
