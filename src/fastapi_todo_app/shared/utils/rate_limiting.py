"""
Rate limiting service with multiple strategies
"""

import time
import asyncio
from typing import Dict, Optional, Tuple, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from enum import Enum
import hashlib
import logging

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"


@dataclass
class RateLimit:
    """Rate limit configuration"""
    requests: int
    window: int  # seconds
    strategy: RateLimitStrategy = RateLimitStrategy.TOKEN_BUCKET


@dataclass
class RateLimitResult:
    """Rate limit check result"""
    allowed: bool
    remaining: int
    reset_time: float
    retry_after: Optional[int] = None


class TokenBucket:
    """Token bucket implementation"""
    
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens"""
        now = time.time()
        self._refill(now)
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self, now: float):
        """Refill tokens based on elapsed time"""
        if now > self.last_refill:
            elapsed = now - self.last_refill
            tokens_to_add = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
    
    @property
    def remaining_tokens(self) -> int:
        now = time.time()
        self._refill(now)
        return int(self.tokens)


class SlidingWindow:
    """Sliding window implementation"""
    
    def __init__(self, capacity: int, window: int):
        self.capacity = capacity
        self.window = window
        self.requests = deque()
    
    def is_allowed(self) -> Tuple[bool, int]:
        """Check if request is allowed"""
        now = time.time()
        cutoff = now - self.window
        
        # Remove old requests
        while self.requests and self.requests[0] <= cutoff:
            self.requests.popleft()
        
        # Check capacity
        if len(self.requests) < self.capacity:
            self.requests.append(now)
            return True, self.capacity - len(self.requests)
        
        return False, 0
    
    @property
    def remaining(self) -> int:
        now = time.time()
        cutoff = now - self.window
        
        # Remove old requests
        while self.requests and self.requests[0] <= cutoff:
            self.requests.popleft()
        
        return max(0, self.capacity - len(self.requests))


class FixedWindow:
    """Fixed window implementation"""
    
    def __init__(self, capacity: int, window: int):
        self.capacity = capacity
        self.window = window
        self.count = 0
        self.window_start = time.time()
    
    def is_allowed(self) -> Tuple[bool, int, float]:
        """Check if request is allowed"""
        now = time.time()
        
        # Reset window if expired
        if now >= self.window_start + self.window:
            self.count = 0
            self.window_start = now
        
        # Check capacity
        if self.count < self.capacity:
            self.count += 1
            reset_time = self.window_start + self.window
            return True, self.capacity - self.count, reset_time
        
        reset_time = self.window_start + self.window
        return False, 0, reset_time


class RateLimitService:
    """Rate limiting service with multiple strategies"""
    
    def __init__(self):
        self._buckets: Dict[str, TokenBucket] = {}
        self._windows: Dict[str, SlidingWindow] = {}
        self._fixed_windows: Dict[str, FixedWindow] = {}
    
    def check_rate_limit(
        self, 
        identifier: str, 
        rate_limit: RateLimit,
        tokens: int = 1
    ) -> RateLimitResult:
        """Check if request is within rate limit"""
        
        if rate_limit.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._check_token_bucket(identifier, rate_limit, tokens)
        elif rate_limit.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._check_sliding_window(identifier, rate_limit)
        elif rate_limit.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._check_fixed_window(identifier, rate_limit)
        else:
            raise ValueError(f"Unknown rate limit strategy: {rate_limit.strategy}")
    
    def _check_token_bucket(
        self, 
        identifier: str, 
        rate_limit: RateLimit, 
        tokens: int
    ) -> RateLimitResult:
        """Check token bucket rate limit"""
        bucket_key = f"bucket:{identifier}:{rate_limit.requests}:{rate_limit.window}"
        
        if bucket_key not in self._buckets:
            refill_rate = rate_limit.requests / rate_limit.window
            self._buckets[bucket_key] = TokenBucket(rate_limit.requests, refill_rate)
        
        bucket = self._buckets[bucket_key]
        allowed = bucket.consume(tokens)
        remaining = bucket.remaining_tokens
        reset_time = time.time() + (rate_limit.requests - remaining) / (rate_limit.requests / rate_limit.window)
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=int(reset_time - time.time()) if not allowed else None
        )
    
    def _check_sliding_window(
        self, 
        identifier: str, 
        rate_limit: RateLimit
    ) -> RateLimitResult:
        """Check sliding window rate limit"""
        window_key = f"sliding:{identifier}:{rate_limit.requests}:{rate_limit.window}"
        
        if window_key not in self._windows:
            self._windows[window_key] = SlidingWindow(rate_limit.requests, rate_limit.window)
        
        window = self._windows[window_key]
        allowed, remaining = window.is_allowed()
        reset_time = time.time() + rate_limit.window
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=rate_limit.window if not allowed else None
        )
    
    def _check_fixed_window(
        self, 
        identifier: str, 
        rate_limit: RateLimit
    ) -> RateLimitResult:
        """Check fixed window rate limit"""
        fixed_key = f"fixed:{identifier}:{rate_limit.requests}:{rate_limit.window}"
        
        if fixed_key not in self._fixed_windows:
            self._fixed_windows[fixed_key] = FixedWindow(rate_limit.requests, rate_limit.window)
        
        window = self._fixed_windows[fixed_key]
        allowed, remaining, reset_time = window.is_allowed()
        
        return RateLimitResult(
            allowed=allowed,
            remaining=remaining,
            reset_time=reset_time,
            retry_after=int(reset_time - time.time()) if not allowed else None
        )
    
    def get_identifier(self, request) -> str:
        """Generate identifier for rate limiting"""
        # Try to get user ID from request
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"
    
    def cleanup_expired(self):
        """Cleanup expired rate limit entries"""
        # This could be enhanced to remove old entries periodically
        pass


# Global rate limit service
rate_limit_service = RateLimitService()


# Common rate limit configurations
class CommonRateLimits:
    """Common rate limit configurations"""
    
    # API endpoints
    API_DEFAULT = RateLimit(requests=100, window=60)  # 100 requests per minute
    API_AUTH = RateLimit(requests=10, window=60)      # 10 login attempts per minute
    API_HEAVY = RateLimit(requests=10, window=300)    # 10 heavy operations per 5 minutes
    
    # User actions
    USER_ACTIONS = RateLimit(requests=1000, window=3600)  # 1000 actions per hour
    USER_CREATION = RateLimit(requests=5, window=300)     # 5 creates per 5 minutes
    
    # Search and queries
    SEARCH_QUERIES = RateLimit(requests=50, window=60)    # 50 searches per minute