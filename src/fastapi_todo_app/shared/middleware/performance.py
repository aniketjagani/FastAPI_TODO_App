"""
Performance monitoring and metrics middleware
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import time
import logging
import asyncio
from typing import Callable

logger = logging.getLogger(__name__)


class PerformanceMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request performance and metrics"""
    
    def __init__(self, app, slow_request_threshold: float = 1.0):
        super().__init__(app)
        self.slow_request_threshold = slow_request_threshold
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start timing
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate metrics
        process_time = time.time() - start_time
        
        # Add performance headers
        response.headers["X-Process-Time"] = f"{process_time:.4f}"
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "unknown")
        
        # Log slow requests
        if process_time > self.slow_request_threshold:
            logger.warning(
                f"Slow request detected: {request.method} {request.url} - {process_time:.4f}s"
            )
        
        # Log request completion
        logger.info(
            f"{request.method} {request.url} - {response.status_code} - {process_time:.4f}s"
        )
        
        return response


class DatabaseMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking database connection metrics"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Add database connection info to request state if needed
        request.state.db_connections_before = self._get_active_connections()
        
        response = await call_next(request)
        
        # Check for connection leaks
        connections_after = self._get_active_connections()
        if connections_after > request.state.db_connections_before + 5:  # Threshold
            logger.warning(f"Potential connection leak detected: {connections_after} active connections")
        
        response.headers["X-DB-Connections"] = str(connections_after)
        
        return response
    
    def _get_active_connections(self) -> int:
        """Get current active database connections"""
        # This would connect to your actual connection pool
        # For now, return a placeholder
        return 0


class CacheMetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking cache performance"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Initialize cache metrics
        request.state.cache_hits = 0
        request.state.cache_misses = 0
        
        response = await call_next(request)
        
        # Add cache metrics to response headers
        cache_hit_ratio = (
            request.state.cache_hits / 
            (request.state.cache_hits + request.state.cache_misses)
            if (request.state.cache_hits + request.state.cache_misses) > 0 else 0
        )
        
        response.headers["X-Cache-Hit-Ratio"] = f"{cache_hit_ratio:.2f}"
        response.headers["X-Cache-Hits"] = str(request.state.cache_hits)
        response.headers["X-Cache-Misses"] = str(request.state.cache_misses)
        
        return response
