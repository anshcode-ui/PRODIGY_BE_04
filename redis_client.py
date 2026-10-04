import os
import json
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", 60))

# Initialize Redis client with connection pooling
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    decode_responses=True
)


def get_cache(key: str):
    """Retrieve and deserialize JSON data from Redis."""
    try:
        data = redis_client.get(key)
        return json.loads(data) if data else None
    except redis.RedisError:
        return None


def set_cache(key: str, value: any, ttl: int = CACHE_TTL):
    """Serialize and write key-value pair to Redis with TTL expiration."""
    try:
        redis_client.setex(key, ttl, json.dumps(value))
    except redis.RedisError:
        pass


def delete_cache_pattern(pattern: str):
    """Invalidate all keys matching the provided pattern."""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            redis_client.delete(*keys)
    except redis.RedisError:
        pass