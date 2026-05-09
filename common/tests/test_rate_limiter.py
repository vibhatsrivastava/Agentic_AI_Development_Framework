"""
test_rate_limiter.py — Tests for common.rate_limiter module.
"""

import pytest
import time
import threading
from common.rate_limiter import (
    TokenBucketRateLimiter,
    get_ollama_rate_limiter,
    configure_ollama_rate_limiter
)
from common.exceptions import RateLimitError


class TestTokenBucketRateLimiter:
    """Test suite for TokenBucketRateLimiter."""
    
    def test_initialize_limiter(self):
        """Test rate limiter initialization."""
        limiter = TokenBucketRateLimiter(tokens_per_second=5.0, bucket_capacity=10)
        assert limiter.tokens_per_second == 5.0
        assert limiter.bucket_capacity == 10
        assert limiter.tokens == 10.0  # Starts full
    
    def test_acquire_single_token(self):
        """Test acquiring a single token."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10.0, bucket_capacity=10)
        
        result = limiter.acquire(tokens=1, block=False)
        assert result is True
        assert limiter.tokens == 9.0
    
    def test_acquire_multiple_tokens(self):
        """Test acquiring multiple tokens."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10.0, bucket_capacity=10)
        
        result = limiter.acquire(tokens=5, block=False)
        assert result is True
        assert limiter.tokens == 5.0
    
    def test_acquire_exceeds_available_non_blocking(self):
        """Test acquiring more tokens than available (non-blocking)."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10.0, bucket_capacity=5)
        
        # Acquire all tokens
        limiter.acquire(tokens=5, block=False)
        
        # Try to acquire more - should raise RateLimitError
        with pytest.raises(RateLimitError) as exc_info:
            limiter.acquire(tokens=1, block=False)
        
        assert exc_info.value.retry_after > 0
    
    def test_acquire_blocking_with_refill(self):
        """Test blocking acquire waits for token refill."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100.0, bucket_capacity=2)
        
        # Acquire all tokens
        limiter.acquire(tokens=2, block=False)
        assert limiter.tokens == 0.0
        
        # This should block briefly then succeed
        start = time.time()
        result = limiter.acquire(tokens=1, block=True)
        

        elapsed = time.time() - start
        
        assert result is True
        # Should have waited for refill (at 100 tokens/sec, 1 token needs 0.01s)
        assert elapsed >= 0.01
    
    def test_acquire_with_timeout(self):
        """Test blocking acquire with timeout."""
        limiter = TokenBucketRateLimiter(tokens_per_second=1.0, bucket_capacity=1)
        
        # Acquire all tokens
        limiter.acquire(tokens=1, block=False)
        
        # Try to acquire with short timeout - should fail
        result = limiter.acquire(tokens=1, block=True, timeout=0.1)
        assert result is False
    
    def test_get_available_tokens(self):
        """Test getting available token count."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10.0, bucket_capacity=20)
        
        # Start with full bucket
        assert limiter.get_available_tokens() == 20.0
        
        # Acquire some tokens
        limiter.acquire(tokens=5, block=False)
        # Use pytest.approx to handle timing precision issues
        assert pytest.approx(limiter.get_available_tokens(), abs=0.1) == 15.0
    
    def test_token_refill_over_time(self):
        """Test that tokens refill over time."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100.0, bucket_capacity=10)
        
        # Acquire all tokens
        limiter.acquire(tokens=10, block=False)
        assert limiter.tokens == 0.0
        
        # Wait for refill
        time.sleep(0.1)  # Should refill 10 tokens at 100/sec
        
        available = limiter.get_available_tokens()
        assert available >= 9.0  # Allow some timing variance
    
    def test_token_refill_caps_at_capacity(self):
        """Test that token refill doesn't exceed bucket capacity."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100.0, bucket_capacity=5)
        
        # Start with partial tokens
        limiter.tokens = 2.0
        
        # Wait longer than needed to fill
        time.sleep(0.1)  # Would refill 10 tokens but cap is 5
        
        available = limiter.get_available_tokens()
        assert available <= 5.0
    
    def test_reset(self):
        """Test resetting the rate limiter."""
        limiter = TokenBucketRateLimiter(tokens_per_second=10.0, bucket_capacity=20)
        
        # Acquire some tokens
        limiter.acquire(tokens=15, block=False)
        assert limiter.tokens == 5.0
        
        # Reset
        limiter.reset()
        assert limiter.tokens == 20.0
    
    def test_thread_safety(self):
        """Test that rate limiter is thread-safe."""
        limiter = TokenBucketRateLimiter(tokens_per_second=100.0, bucket_capacity=50)
        results = []
        
        def acquire_token():
            try:
                limiter.acquire(tokens=1, block=True, timeout=1.0)
                results.append(True)
            except Exception:
                results.append(False)
        
        # Create multiple threads trying to acquire tokens
        threads = [threading.Thread(target=acquire_token) for _ in range(50)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All should succeed (50 tokens available, 50 threads)
        assert all(results)
        assert len(results) == 50


class TestGlobalOllamaRateLimiter:
    """Test suite for global Ollama rate limiter functions."""
    
    def test_get_ollama_rate_limiter(self):
        """Test getting global Ollama rate limiter."""
        limiter = get_ollama_rate_limiter()
        
        assert limiter is not None
        assert isinstance(limiter, TokenBucketRateLimiter)
        assert limiter.tokens_per_second == 10.0
        assert limiter.bucket_capacity == 20
    
    def test_get_ollama_rate_limiter_singleton(self):
        """Test that get_ollama_rate_limiter returns the same instance."""
        limiter1 = get_ollama_rate_limiter()
        limiter2 = get_ollama_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_configure_ollama_rate_limiter(self):
        """Test configuring global Ollama rate limiter."""
        configure_ollama_rate_limiter(tokens_per_second=5.0, bucket_capacity=10)
        
        limiter = get_ollama_rate_limiter()
        assert limiter.tokens_per_second == 5.0
        assert limiter.bucket_capacity == 10
        
        # Reset to default for other tests
        configure_ollama_rate_limiter(tokens_per_second=10.0, bucket_capacity=20)
