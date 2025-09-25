"""
API response optimization and streaming utilities
"""

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List, Optional, Union
from fastapi import Response, status
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.encoders import jsonable_encoder
import gzip
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class OptimizedJSONResponse(JSONResponse):
    """Optimized JSON response with compression and caching headers"""
    
    def __init__(
        self,
        content: Any = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        media_type: Optional[str] = None,
        enable_compression: bool = True,
        cache_max_age: Optional[int] = None,
        etag: Optional[str] = None,
    ):
        # Convert to JSON-serializable format
        if content is not None:
            content = jsonable_encoder(content)
        
        # Initialize headers
        if headers is None:
            headers = {}
        
        # Add caching headers
        if cache_max_age is not None:
            headers["Cache-Control"] = f"max-age={cache_max_age}, public"
        
        if etag:
            headers["ETag"] = f'"{etag}"'
        
        # Add performance headers
        headers["X-Content-Optimized"] = "true"
        headers["X-Timestamp"] = datetime.now(timezone.utc).isoformat()
        
        super().__init__(content, status_code, headers, media_type)
        
        # Apply compression if enabled and content is large enough
        if enable_compression and content and len(self.body) > 1000:
            self._apply_compression()
    
    def _apply_compression(self):
        """Apply gzip compression to response body"""
        try:
            compressed = gzip.compress(self.body, compresslevel=6)
            if len(compressed) < len(self.body):
                self.body = compressed
                self.headers["Content-Encoding"] = "gzip"
                self.headers["Content-Length"] = str(len(compressed))
                logger.debug(f"Response compressed: {len(self.body)} -> {len(compressed)} bytes")
        except Exception as e:
            logger.warning(f"Compression failed: {e}")


class StreamingJSONResponse(StreamingResponse):
    """Streaming JSON response for large datasets"""
    
    def __init__(
        self,
        content: AsyncGenerator[Any, None],
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        chunk_size: int = 100,
    ):
        if headers is None:
            headers = {}
        
        headers["Content-Type"] = "application/json"
        headers["X-Streaming"] = "true"
        
        # Create streaming generator
        async def generate_stream():
            yield '{"data": ['
            first_item = True
            
            async for item in content:
                if not first_item:
                    yield ","
                yield json.dumps(jsonable_encoder(item))
                first_item = False
            
            yield "]}"
        
        super().__init__(generate_stream(), status_code, headers, media_type="application/json")


class PaginatedResponse:
    """Paginated response utility"""
    
    @staticmethod
    def create(
        data: List[Any],
        total: int,
        page: int,
        page_size: int,
        base_url: str = "",
    ) -> Dict[str, Any]:
        """Create paginated response structure"""
        total_pages = (total + page_size - 1) // page_size
        has_next = page < total_pages
        has_prev = page > 1
        
        response = {
            "data": data,
            "pagination": {
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
            },
            "links": {
                "self": f"{base_url}?page={page}&page_size={page_size}",
                "first": f"{base_url}?page=1&page_size={page_size}",
                "last": f"{base_url}?page={total_pages}&page_size={page_size}",
            }
        }
        
        if has_next:
            response["links"]["next"] = f"{base_url}?page={page + 1}&page_size={page_size}"
        
        if has_prev:
            response["links"]["prev"] = f"{base_url}?page={page - 1}&page_size={page_size}"
        
        return response


class ResponseCache:
    """In-memory response cache for frequently requested data"""
    
    def __init__(self, default_ttl: int = 300):
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached response"""
        if key in self.cache:
            entry = self.cache[key]
            if datetime.now(timezone.utc) < entry["expires"]:
                logger.debug(f"Cache hit: {key}")
                return entry["data"]
            else:
                # Expired entry
                del self.cache[key]
                logger.debug(f"Cache expired: {key}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """Set cached response"""
        ttl = ttl or self.default_ttl
        expires = datetime.now(timezone.utc).timestamp() + ttl
        
        self.cache[key] = {
            "data": data,
            "expires": datetime.fromtimestamp(expires, timezone.utc),
            "created": datetime.now(timezone.utc)
        }
        
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """Delete cached entry"""
        if key in self.cache:
            del self.cache[key]
            logger.debug(f"Cache deleted: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries"""
        self.cache.clear()
        logger.info("Response cache cleared")
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count"""
        now = datetime.now(timezone.utc)
        expired_keys = [
            key for key, entry in self.cache.items()
            if now >= entry["expires"]
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
        
        return len(expired_keys)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        now = datetime.now(timezone.utc)
        active_entries = sum(1 for entry in self.cache.values() if now < entry["expires"])
        expired_entries = len(self.cache) - active_entries
        
        return {
            "total_entries": len(self.cache),
            "active_entries": active_entries,
            "expired_entries": expired_entries,
            "memory_usage_mb": len(str(self.cache)) / (1024 * 1024),  # Rough estimate
        }


class DataCompressor:
    """Data compression utilities for responses"""
    
    @staticmethod
    def compress_json(data: Any, compression_level: int = 6) -> bytes:
        """Compress JSON data using gzip"""
        json_str = json.dumps(jsonable_encoder(data))
        return gzip.compress(json_str.encode('utf-8'), compresslevel=compression_level)
    
    @staticmethod
    def should_compress(content_length: int, threshold: int = 1000) -> bool:
        """Determine if content should be compressed"""
        return content_length >= threshold


# Global instances
response_cache = ResponseCache()


# Response decorators
def cached_response(ttl: int = 300, key_func: Optional[callable] = None):
    """Decorator for caching responses"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_data = response_cache.get(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            response_cache.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


async def stream_large_dataset(
    data_generator: AsyncGenerator[Any, None],
    chunk_size: int = 100
) -> AsyncGenerator[bytes, None]:
    """Stream large datasets in chunks"""
    yield b'{"data": ['
    first = True
    count = 0
    
    async for item in data_generator:
        if not first:
            yield b","
        
        yield json.dumps(jsonable_encoder(item)).encode('utf-8')
        first = False
        count += 1
        
        # Yield control every chunk_size items
        if count % chunk_size == 0:
            await asyncio.sleep(0)  # Allow other tasks to run
    
    yield b"]}"