"""Rate limiting module for Azure drift detection."""

from typing import Dict, Any, Optional, Callable
import time
import threading
from datetime import datetime, timedelta
import logging
from collections import deque

logger = logging.getLogger(__name__)

class RateLimiter:
    """Implements rate limiting for API endpoints."""

    def __init__(self, requests_per_minute: int = 60, burst_size: int = 10):
        """Initialize the rate limiter.
        
        Args:
            requests_per_minute: Maximum requests allowed per minute
            burst_size: Maximum number of requests allowed in burst
        """
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.requests = deque()
        self.lock = threading.Lock()
        self.window_size = 60  # 1 minute window

    def _cleanup_old_requests(self) -> None:
        """Remove requests older than the window size."""
        current_time = time.time()
        while self.requests and current_time - self.requests[0] > self.window_size:
            self.requests.popleft()

    def is_allowed(self) -> bool:
        """Check if a new request is allowed.
        
        Returns:
            bool: True if request is allowed
        """
        with self.lock:
            self._cleanup_old_requests()
            return len(self.requests) < self.requests_per_minute

    def record_request(self) -> None:
        """Record a new request."""
        with self.lock:
            self.requests.append(time.time())

    def get_wait_time(self) -> float:
        """Get the time to wait before next request is allowed.
        
        Returns:
            float: Time to wait in seconds
        """
        with self.lock:
            self._cleanup_old_requests()
            if len(self.requests) < self.requests_per_minute:
                return 0.0
            
            oldest_request = self.requests[0]
            return max(0.0, self.window_size - (time.time() - oldest_request))

    def get_current_rate(self) -> float:
        """Get the current request rate.
        
        Returns:
            float: Current requests per minute
        """
        with self.lock:
            self._cleanup_old_requests()
            return len(self.requests) / (self.window_size / 60)


class TokenBucket:
    """Implements token bucket algorithm for rate limiting."""

    def __init__(self, rate: float, capacity: int):
        """Initialize the token bucket.
        
        Args:
            rate: Tokens added per second
            capacity: Maximum number of tokens
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def _update_tokens(self) -> None:
        """Update the number of tokens based on time passed."""
        now = time.time()
        time_passed = now - self.last_update
        self.tokens = min(
            self.capacity,
            self.tokens + time_passed * self.rate
        )
        self.last_update = now

    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            bool: True if tokens were consumed
        """
        with self.lock:
            self._update_tokens()
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def get_tokens(self) -> float:
        """Get current number of tokens.
        
        Returns:
            float: Current number of tokens
        """
        with self.lock:
            self._update_tokens()
            return self.tokens


class RateLimitMiddleware:
    """Middleware for rate limiting API requests."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the rate limit middleware.
        
        Args:
            config: Rate limiting configuration
        """
        self.rate_limiters: Dict[str, RateLimiter] = {}
        self.token_buckets: Dict[str, TokenBucket] = {}
        self.config = config
        self._setup_limiters()

    def _setup_limiters(self) -> None:
        """Set up rate limiters for each endpoint."""
        for endpoint, limit_config in self.config.items():
            self.rate_limiters[endpoint] = RateLimiter(
                requests_per_minute=limit_config.get("requests_per_minute", 60),
                burst_size=limit_config.get("burst_size", 10)
            )
            self.token_buckets[endpoint] = TokenBucket(
                rate=limit_config.get("rate", 1.0),
                capacity=limit_config.get("capacity", 10)
            )

    def check_rate_limit(self, endpoint: str) -> bool:
        """Check if request to endpoint is allowed.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            bool: True if request is allowed
        """
        limiter = self.rate_limiters.get(endpoint)
        bucket = self.token_buckets.get(endpoint)
        
        if not limiter or not bucket:
            return True
        
        return limiter.is_allowed() and bucket.consume()

    def record_request(self, endpoint: str) -> None:
        """Record a request to an endpoint.
        
        Args:
            endpoint: API endpoint
        """
        limiter = self.rate_limiters.get(endpoint)
        if limiter:
            limiter.record_request()

    def get_wait_time(self, endpoint: str) -> float:
        """Get time to wait before next request to endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            float: Time to wait in seconds
        """
        limiter = self.rate_limiters.get(endpoint)
        if limiter:
            return limiter.get_wait_time()
        return 0.0

    def get_current_rate(self, endpoint: str) -> float:
        """Get current request rate for endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            float: Current requests per minute
        """
        limiter = self.rate_limiters.get(endpoint)
        if limiter:
            return limiter.get_current_rate()
        return 0.0

    def get_remaining_tokens(self, endpoint: str) -> float:
        """Get remaining tokens for endpoint.
        
        Args:
            endpoint: API endpoint
            
        Returns:
            float: Remaining tokens
        """
        bucket = self.token_buckets.get(endpoint)
        if bucket:
            return bucket.get_tokens()
        return 0.0


def rate_limit(requests_per_minute: int = 60, burst_size: int = 10) -> Callable:
    """Decorator for rate limiting function calls.
    
    Args:
        requests_per_minute: Maximum requests allowed per minute
        burst_size: Maximum number of requests allowed in burst
        
    Returns:
        Callable: Decorated function
    """
    limiter = RateLimiter(requests_per_minute, burst_size)
    
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            if not limiter.is_allowed():
                wait_time = limiter.get_wait_time()
                logger.warning(f"Rate limit exceeded. Waiting {wait_time:.2f} seconds")
                time.sleep(wait_time)
            
            limiter.record_request()
            return func(*args, **kwargs)
        return wrapper
    return decorator 