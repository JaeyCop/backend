import redis
import json
import pickle
import logging
from typing import Any, Optional, Union, List
from datetime import timedelta
import asyncio
from functools import wraps

from app.core.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """Enhanced cache manager with Redis backend and fallback to in-memory cache."""
    
    def __init__(self):
        self.redis_client = None
        self.memory_cache = {}
        self.default_ttl = settings.CACHE_TTL
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection with error handling."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=False,  # We'll handle encoding ourselves
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, falling back to memory cache: {e}")
            self.redis_client = None
    
    def _serialize_value(self, value: Any) -> bytes:
        """Serialize value for storage."""
        try:
            # Try JSON first for simple types
            if isinstance(value, (dict, list, str, int, float, bool, type(None))):
                return json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Failed to serialize value: {e}")
            return pickle.dumps(value)
    
    def _deserialize_value(self, value: bytes) -> Any:
        """Deserialize value from storage."""
        try:
            # Try JSON first
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                # Fall back to pickle
                return pickle.loads(value)
            except Exception as e:
                logger.error(f"Failed to deserialize value: {e}")
                return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value is not None:
                    return self._deserialize_value(value)
            else:
                # Fallback to memory cache
                return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL."""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = self._serialize_value(value)
            
            if self.redis_client:
                return self.redis_client.setex(key, ttl, serialized_value)
            else:
                # Fallback to memory cache (no TTL support in simple implementation)
                self.memory_cache[key] = value
                return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            if self.redis_client:
                return bool(self.redis_client.delete(key))
            else:
                return self.memory_cache.pop(key, None) is not None
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            if self.redis_client:
                return bool(self.redis_client.exists(key))
            else:
                return key in self.memory_cache
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            if self.redis_client:
                return bool(self.redis_client.flushdb())
            else:
                self.memory_cache.clear()
                return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_many(self, keys: List[str]) -> dict:
        """Get multiple values from cache."""
        result = {}
        try:
            if self.redis_client:
                values = self.redis_client.mget(keys)
                for key, value in zip(keys, values):
                    if value is not None:
                        result[key] = self._deserialize_value(value)
            else:
                for key in keys:
                    if key in self.memory_cache:
                        result[key] = self.memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
        return result
    
    def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        try:
            ttl = ttl or self.default_ttl
            
            if self.redis_client:
                pipe = self.redis_client.pipeline()
                for key, value in mapping.items():
                    serialized_value = self._serialize_value(value)
                    pipe.setex(key, ttl, serialized_value)
                pipe.execute()
                return True
            else:
                self.memory_cache.update(mapping)
                return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache."""
        try:
            if self.redis_client:
                return self.redis_client.incrby(key, amount)
            else:
                current = self.memory_cache.get(key, 0)
                new_value = current + amount
                self.memory_cache[key] = new_value
                return new_value
        except Exception as e:
            logger.error(f"Cache increment error for key '{key}': {e}")
            return None
    
    def get_stats(self) -> dict:
        """Get cache statistics."""
        try:
            if self.redis_client:
                info = self.redis_client.info()
                return {
                    "backend": "redis",
                    "connected_clients": info.get("connected_clients", 0),
                    "used_memory": info.get("used_memory_human", "0B"),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0)
                }
            else:
                return {
                    "backend": "memory",
                    "total_keys": len(self.memory_cache),
                    "memory_usage": "unknown"
                }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}


# Global cache instance
cache = CacheManager()


def cache_result(key_prefix: str, ttl: Optional[int] = None):
    """Decorator to cache function results."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss, stored result for key: {cache_key}")
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            logger.debug(f"Cache miss, stored result for key: {cache_key}")
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate cache keys matching a pattern."""
    try:
        if cache.redis_client:
            keys = cache.redis_client.keys(pattern)
            if keys:
                return cache.redis_client.delete(*keys)
        else:
            # For memory cache, we need to iterate through keys
            keys_to_delete = [key for key in cache.memory_cache.keys() if pattern in key]
            for key in keys_to_delete:
                del cache.memory_cache[key]
            return len(keys_to_delete)
    except Exception as e:
        logger.error(f"Cache pattern invalidation error: {e}")
    return 0


# Cache key generators
class CacheKeys:
    """Cache key generators for different data types."""
    
    @staticmethod
    def recipe_search(query: str, limit: int, include_videos: bool) -> str:
        return f"recipe:search:{hash(query)}:{limit}:{include_videos}"
    
    @staticmethod
    def recipe_detail(url: str) -> str:
        return f"recipe:detail:{hash(url)}"
    
    @staticmethod
    def user_profile(user_id: int) -> str:
        return f"user:profile:{user_id}"
    
    @staticmethod
    def user_stats(user_id: int) -> str:
        return f"user:stats:{user_id}"
    
    @staticmethod
    def trending_recipes() -> str:
        return "recipes:trending"
    
    @staticmethod
    def popular_recipes() -> str:
        return "recipes:popular"
    
    @staticmethod
    def video_search(query: str, max_results: int) -> str:
        return f"videos:search:{hash(query)}:{max_results}"


# Rate limiting using cache
class RateLimiter:
    """Simple rate limiter using cache backend."""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """Check if request is allowed within rate limit."""
        try:
            current = self.cache.get(key) or 0
            if current >= limit:
                return False
            
            # Increment counter
            new_count = self.cache.increment(key) or 1
            if new_count == 1:
                # Set TTL for new key
                self.cache.set(key, 1, window)
            
            return new_count <= limit
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Allow on error


# Global rate limiter
rate_limiter = RateLimiter(cache)
