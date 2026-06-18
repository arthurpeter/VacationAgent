import inspect

import redis.asyncio as redis
import json
import functools
from app.core.config import settings
from app.core.logger import get_logger

log = get_logger(__name__)

r = redis.Redis(
    host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0, decode_responses=True
)
log.info(f"Connected to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}")


def redis_cache(expire_time=1800):
    """
    A hybrid custom decorator that transparently caches the results of
    both synchronous and asynchronous functions in Redis.
    """

    def decorator(func):
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                key_parts = (
                    [func.__name__]
                    + [str(arg) for arg in args]
                    + [f"{k}={v}" for k, v in kwargs.items()]
                )
                cache_key = ":".join(key_parts)

                try:
                    cached_data = await r.get(cache_key)
                    if cached_data:
                        log.info(f"Cache HIT: Serving {cache_key} from Redis")
                        return json.loads(cached_data)
                except redis.ConnectionError:
                    log.error(
                        f"Redis at {settings.REDIS_HOST} is down, skipping cache check."
                    )

                log.warning(f"Cache MISS: Fetching live data async for {cache_key}")

                result = await func(*args, **kwargs)

                try:
                    if result is not None:
                        await r.setex(cache_key, expire_time, json.dumps(result))
                except Exception as e:
                    log.error(
                        f"Failed to commit async payload cache data to Redis: {e}"
                    )

                return result

            return async_wrapper

    return decorator
