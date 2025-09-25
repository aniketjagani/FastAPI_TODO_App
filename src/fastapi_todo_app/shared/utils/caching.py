"""
Enhanced caching service with Redis integration
"""

import json
import pickle
from typing import Any, Optional, Union, Dict, List
from functools import wraps
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CacheService:
    """Enhanced caching service with Redis and in-memory fallback"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 300):
        self.default_ttl = default_ttl
        self.redis_client = None
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        
        if REDIS_AVAILABLE and redis_url:
            self.redis_client = redis.from_url(redis_url)
            logger.info("Redis cache initialized")
        else:
            logger.warning("Redis not available, using in-memory cache fallback")
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        try:
            if self.redis_client:
                value = await self.redis_client.get(key)
                if value:
                    return pickle.loads(value)
            else:
                # Memory cache fallback
                cache_entry = self._memory_cache.get(key)
                if cache_entry and cache_entry["expires"] > datetime.now():
                    return cache_entry["value"]
                elif cache_entry:
                    # Expired entry
                    del self._memory_cache[key]
            
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        try:
            ttl = ttl or self.default_ttl
            
            if self.redis_client:
                serialized_value = pickle.dumps(value)
                await self.redis_client.setex(key, ttl, serialized_value)
            else:
                # Memory cache fallback
                self._memory_cache[key] = {
                    "value": value,
                    "expires": datetime.now() + timedelta(seconds=ttl)
                }
            
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            if self.redis_client:
                await self.redis_client.delete(key)
            else:
                self._memory_cache.pop(key, None)
            
            return True
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    async def clear(self) -> bool:
        """Clear all cache"""
        try:
            if self.redis_client:
                await self.redis_client.flushdb()
            else:
                self._memory_cache.clear()
            
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{':'.join(map(str, args))}"
        if kwargs:
            key_data += f":{':'.join(f'{k}={v}' for k, v in sorted(kwargs.items()))}"
        
        return hashlib.md5(key_data.encode()).hexdigest()


# Global cache instance
cache_service = CacheService()


def cached(ttl: int = 300, key_prefix: str = "default"):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service.generate_key(key_prefix, func.__name__, *args, **kwargs)
            
            # Try to get from cache
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for key: {cache_key}")
                return cached_result
            
            # Execute function and cache result
            logger.debug(f"Cache miss for key: {cache_key}")
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


class CacheStats:
    """Cache statistics tracking"""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
    
    def record_hit(self):
        self.hits += 1
    
    def record_miss(self):
        self.misses += 1
    
    def record_error(self):
        self.errors += 1
    
    @property
    def hit_ratio(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_ratio": self.hit_ratio
        }


# Global cache stats
cache_stats = CacheStats()