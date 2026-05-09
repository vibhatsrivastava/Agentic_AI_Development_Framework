"""
test_retry.py — Tests for common.retry module.
"""

import pytest
import time
from unittest.mock import Mock
from common.retry import (
    retry_with_exponential_backoff,
    retry_on_connection_error,
    retry_on_rate_limit
)
from common.exceptions import RateLimitError, OllamaConnectionError


class TestRetryWithExponentialBackoff:
    """Test suite for retry_with_exponential_backoff decorator."""
    
    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        mock_func = Mock(return_value="success")
        
        @retry_with_exponential_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_exception(self):
        """Test that function retries on exception."""
        mock_func = Mock(side_effect=[ValueError("error"), ValueError("error"), "success"])
        
        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01,  # Short delay for tests
            exceptions=(ValueError,)
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries exceeded."""
        mock_func = Mock(side_effect=ValueError("persistent error"))
        
        @retry_with_exponential_backoff(
            max_retries=2,
            initial_delay=0.01,
            exceptions=(ValueError,)
        )
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError, match="persistent error"):
            test_func()
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    def test_exponential_backoff_timing(self):
        """Test that delays increase exponentially."""
        call_times = []
        
        def failing_func():
            call_times.append(time.time())
            raise ValueError("error")
        
        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.1,
            exponential_base=2.0,
            exceptions=(ValueError,)
        )
        def test_func():
            return failing_func()
        
        with pytest.raises(ValueError):
            test_func()
        
        # Check that delays roughly doubled each time
        assert len(call_times) == 4  # Initial + 3 retries
        
        # First retry delay ~0.1s
        delay1 = call_times[1] - call_times[0]
        assert 0.08 <= delay1 <= 0.15
        
        # Second retry delay ~0.2s
        delay2 = call_times[2] - call_times[1]
        assert 0.18 <= delay2 <= 0.25
    
    def test_max_delay_cap(self):
        """Test that delay is capped at max_delay."""
        call_times = []
        
        def failing_func():
            call_times.append(time.time())
            raise ValueError("error")
        
        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=1.0,
            max_delay=0.5,  # Cap at 0.5s
            exceptions=(ValueError,)
        )
        def test_func():
            return failing_func()
        
        with pytest.raises(ValueError):
            test_func()
        
        # First retry should use max_delay (0.5s) since initial_delay (1.0s) > max_delay
        # Subsequent delays should also be capped at 0.5s
        for i in range(1, len(call_times)):
            delay = call_times[i] - call_times[i-1]
            # Allow some timing tolerance (execution overhead, sleep precision)
            assert delay <= 0.7, f"Delay {delay:.3f}s exceeded cap (expected <=0.5s + tolerance)"
    
    def test_rate_limit_error_handling(self):
        """Test special handling for RateLimitError."""
        mock_func = Mock(
            side_effect=[
                RateLimitError("Rate limited", retry_after=0.05),
                "success"
            ]
        )
        
        @retry_with_exponential_backoff(
            max_retries=2,
            initial_delay=1.0  # Should use retry_after instead
        )
        def test_func():
            return mock_func()
        
        start = time.time()
        result = test_func()
        elapsed = time.time() - start
        
        assert result == "success"
        assert mock_func.call_count == 2
        # Should have used retry_after (0.05s) not initial_delay (1.0s)
        assert elapsed < 0.5
    
    def test_on_retry_callback(self):
        """Test that on_retry callback is called."""
        retry_info = []
        
        def on_retry_callback(exception, attempt):
            retry_info.append((str(exception), attempt))
        
        mock_func = Mock(side_effect=[ValueError("error1"), ValueError("error2"), "success"])
        
        @retry_with_exponential_backoff(
            max_retries=3,
            initial_delay=0.01,
            exceptions=(ValueError,),
            on_retry=on_retry_callback
        )
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert len(retry_info) == 2  # 2 failures before success
        assert retry_info[0] == ("error1", 1)
        assert retry_info[1] == ("error2", 2)
    
    def test_only_retries_specified_exceptions(self):
        """Test that only specified exceptions trigger retries."""
        mock_func = Mock(side_effect=TypeError("wrong type"))
        
        @retry_with_exponential_backoff(
            max_retries=3,
            exceptions=(ValueError,)  # Only retry on ValueError
        )
        def test_func():
            return mock_func()
        
        # TypeError should not be retried, raised immediately
        with pytest.raises(TypeError):
            test_func()
        
        assert mock_func.call_count == 1  # No retries


class TestConvenienceDecorators:
    """Test suite for convenience retry decorators."""
    
    def test_retry_on_connection_error(self):
        """Test retry_on_connection_error decorator."""
        mock_func = Mock(side_effect=[ConnectionError("network error"), "success"])
        
        @retry_on_connection_error(max_retries=2)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_on_connection_error_timeout(self):
        """Test retry_on_connection_error with TimeoutError."""
        mock_func = Mock(side_effect=[TimeoutError("timeout"), "success"])
        
        @retry_on_connection_error(max_retries=2)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_on_connection_error_ollama(self):
        """Test retry_on_connection_error with OllamaConnectionError."""
        mock_func = Mock(side_effect=[OllamaConnectionError("can't connect"), "success"])
        
        @retry_on_connection_error(max_retries=2)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_on_rate_limit_decorator(self):
        """Test retry_on_rate_limit decorator."""
        mock_func = Mock(
            side_effect=[
                RateLimitError("Rate limited", retry_after=0.01),
                "success"
            ]
        )
        
        @retry_on_rate_limit(max_retries=2)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_retry_on_rate_limit_longer_delays(self):
        """Test that retry_on_rate_limit uses longer initial delay."""
        call_times = []
        
        def failing_func():
            call_times.append(time.time())
            raise RateLimitError("Rate limited")
        
        @retry_on_rate_limit(max_retries=1, initial_delay=0.2)
        def test_func():
            return failing_func()
        
        with pytest.raises(RateLimitError):
            test_func()
        
        # Check that initial delay was ~0.2s (longer than default)
        delay = call_times[1] - call_times[0]
        assert 0.18 <= delay <= 0.25
