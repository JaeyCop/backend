import json
import pickle
import logging
import hashlib # Added for MD5 hashing
from typing import Any, Optional, List
from datetime import timedelta
import asyncio
from functools import wraps

from app.core.settings import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """In-memory cache manager."""
    
    def __init__(self):
        self.memory_cache = {}
        self.default_ttl = 3600 # Default TTL for in-memory cache (1 hour)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            return self.memory_cache.get(key)
        except Exception as e:
            logger.error(f"Cache get error for key '{key}': {e}")
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with optional TTL (not fully supported in simple in-memory)."""
        try:
            self.memory_cache[key] = value
            return True
        except Exception as e:
            logger.error(f"Cache set error for key '{key}': {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return self.memory_cache.pop(key, None) is not None
        except Exception as e:
            logger.error(f"Cache delete error for key '{key}': {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        try:
            return key in self.memory_cache
        except Exception as e:
            logger.error(f"Cache exists error for key '{key}': {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        try:
            self.memory_cache.clear()
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_many(self, keys: List[str]) -> dict:
        """Get multiple values from cache."""
        result = {}
        try:
            for key in keys:
                if key in self.memory_cache:
                    result[key] = self.memory_cache[key]
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
        return result
    
    def set_many(self, mapping: dict, ttl: Optional[int] = None) -> bool:
        """Set multiple values in cache."""
        try:
            self.memory_cache.update(mapping)
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a numeric value in cache."""
        try:
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
            return {
                "backend": "memory",
                "total_keys": len(self.memory_cache),
                "memory_usage": "unknown" # Cannot easily determine for simple dict
            }
        except Exception as e:
            logger.error(f"Cache stats error: {e}")
            return {"error": str(e)}


# Global cache instance
cache = CacheManager()


def generate_cache_key(*args: Any) -> str:
    """Generates a consistent cache key from a set of arguments."""
    # Convert all arguments to strings and join them
    key_string = "_".join(str(arg) for arg in args if arg is not None)
    # Use MD5 hash for a compact and consistent key
    return hashlib.md5(key_string.encode('utf-8')).hexdigest()


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
            # TTL is not directly supported in this simple in-memory cache for rate limiting
            # The window parameter will effectively be ignored for in-memory rate limiting
            
            return new_count <= limit
        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            return True  # Allow on error


# Global rate limiter
rate_limiter = RateLimiter(cache)
