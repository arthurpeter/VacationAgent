import redis
import json
import functools
from app.core.config import settings

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

def redis_cache(expire_time=1800):
    """
    A custom decorator that caches the result of a function in Redis.
    expire_time: Time in seconds (default 30 mins)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [func.__name__] + [str(arg) for arg in args] + [f"{k}={v}" for k, v in kwargs.items()]
            cache_key = ":".join(key_parts)

            try:
                cached_data = r.get(cache_key)
                if cached_data:
                    print(f"✅ Cache HIT: Serving {cache_key} from Redis")
                    return json.loads(cached_data)
            except redis.ConnectionError:
                print("⚠️ Redis is down, skipping cache.")

            print(f"miss Cache MISS: Calling API for {cache_key}")
            result = func(*args, **kwargs)

            try:
                r.setex(cache_key, expire_time, json.dumps(result))
            except Exception as e:
                print(f"Failed to cache data: {e}")

            return result
        return wrapper
    return decorator