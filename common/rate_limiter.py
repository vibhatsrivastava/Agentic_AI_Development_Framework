"""
rate_limiter.py — Token bucket rate limiter for Ollama API calls.

Prevents exceeding API rate limits by throttling requests using a token bucket algorithm.
Integrates with common.utils.get_logger() for visibility into rate limiting events.
"""

import time
import threading
from typing import Optional
from .exceptions import RateLimitError
from .utils import get_logger

logger = get_logger(__name__)


class TokenBucketRateLimiter:
    """
    Thread-safe token bucket rate limiter for API calls.
    
    The token bucket algorithm allows bursts of requests up to the bucket capacity,
    while enforcing an average rate over time.
    
    Args:
        tokens_per_second: Maximum average request rate (tokens refilled per second)
        bucket_capacity: Maximum burst size (tokens that can accumulate)
    
    Example:
        # Allow 10 requests per second with bursts up to 20
        limiter = TokenBucketRateLimiter(tokens_per_second=10, bucket_capacity=20)
        
        # Before making an API call
        limiter.acquire()  # Blocks if rate limit would be exceeded
        response = api_call()
    """
    
    def __init__(self, tokens_per_second: float = 10.0, bucket_capacity: int = 20):
        """
        Initialize the rate limiter.
        
        Args:
            tokens_per_second: Rate at which tokens are added (default: 10)
            bucket_capacity: Maximum tokens in bucket (default: 20)
        """
        self.tokens_per_second = tokens_per_second
        self.bucket_capacity = bucket_capacity
        self.tokens = float(bucket_capacity)  # Start with full bucket
        self.last_update = time.time()
        self.lock = threading.Lock()
        
        logger.debug(
            f"Rate limiter initialized: {tokens_per_second} tokens/sec, "
            f"capacity: {bucket_capacity}"
        )
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on time elapsed since last update."""
        now = time.time()
        elapsed = now - self.last_update
        
        # Add tokens based on elapsed time
        tokens_to_add = elapsed * self.tokens_per_second
        self.tokens = min(self.bucket_capacity, self.tokens + tokens_to_add)
        self.last_update = now
    
    def acquire(self, tokens: int = 1, block: bool = True, timeout: Optional[float] = None) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire (default: 1)
            block: If True, wait until tokens are available. If False, return immediately.
            timeout: Maximum time to wait in seconds (None = wait forever)
        
        Returns:
            True if tokens were acquired, False if timeout occurred (only when block=True)
        
        Raises:
            RateLimitError: If block=False and tokens are not available
        """
        start_time = time.time()
        
        while True:
            with self.lock:
                self._refill_tokens()
                
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    logger.debug(f"Acquired {tokens} token(s), {self.tokens:.2f} remaining")
                    return True
                
                # Not enough tokens
                if not block:
                    wait_time = (tokens - self.tokens) / self.tokens_per_second
                    raise RateLimitError(
                        f"Rate limit exceeded. {tokens} tokens required, "
                        f"{self.tokens:.2f} available.",
                        retry_after=wait_time
                    )
                
                # Check timeout
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        logger.warning(f"Rate limiter timeout after {elapsed:.2f}s")
                        return False
            
            # Wait a short time before retrying
            time.sleep(0.01)
    
    def get_available_tokens(self) -> float:
        """
        Get the current number of available tokens without acquiring.
        
        Returns:
            Current token count
        """
        with self.lock:
            self._refill_tokens()
            return self.tokens
    
    def reset(self) -> None:
        """Reset the bucket to full capacity."""
        with self.lock:
            self.tokens = float(self.bucket_capacity)
            self.last_update = time.time()
            logger.debug("Rate limiter reset to full capacity")


# Global rate limiter instance for Ollama API calls
# Can be reconfigured by projects that need different limits
_ollama_rate_limiter: Optional[TokenBucketRateLimiter] = None


def get_ollama_rate_limiter() -> TokenBucketRateLimiter:
    """
    Get the global Ollama API rate limiter instance.
    
    Creates a default rate limiter on first use:
    - 10 requests per second average
    - Bursts up to 20 requests
    
    Returns:
        Global TokenBucketRateLimiter instance
    
    Example:
        from common.rate_limiter import get_ollama_rate_limiter
        
        limiter = get_ollama_rate_limiter()
        limiter.acquire()  # Wait for rate limit token
        response = llm.invoke(prompt)
    """
    global _ollama_rate_limiter
    
    if _ollama_rate_limiter is None:
        _ollama_rate_limiter = TokenBucketRateLimiter(
            tokens_per_second=10.0,
            bucket_capacity=20
        )
        logger.info("Global Ollama rate limiter created (10 req/sec, burst: 20)")
    
    return _ollama_rate_limiter


def configure_ollama_rate_limiter(tokens_per_second: float, bucket_capacity: int) -> None:
    """
    Configure the global Ollama rate limiter with custom settings.
    
    Args:
        tokens_per_second: Maximum average request rate
        bucket_capacity: Maximum burst size
    
    Example:
        # Limit to 5 requests/second with smaller bursts
        configure_ollama_rate_limiter(tokens_per_second=5, bucket_capacity=10)
    """
    global _ollama_rate_limiter
    
    _ollama_rate_limiter = TokenBucketRateLimiter(
        tokens_per_second=tokens_per_second,
        bucket_capacity=bucket_capacity
    )
    logger.info(
        f"Ollama rate limiter configured: {tokens_per_second} req/sec, "
        f"burst: {bucket_capacity}"
    )
