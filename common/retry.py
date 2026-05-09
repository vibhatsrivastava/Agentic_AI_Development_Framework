"""
retry.py — Exponential backoff retry decorator for transient failures.

Provides robust retry logic for API calls that may fail temporarily due to
network issues, rate limits, or server errors. Integrates with rate_limiter.py
to handle rate limit exceptions gracefully.
"""

import time
import functools
from typing import Callable, Type, Tuple, Optional
from .exceptions import RateLimitError
from .utils import get_logger

logger = get_logger(__name__)


def retry_with_exponential_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    exponential_base: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Decorator that retries a function with exponential backoff on failure.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds before first retry (default: 1.0)
        exponential_base: Multiplier for delay after each retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
        on_retry: Optional callback function(exception, attempt_number) called before each retry
    
    Returns:
        Decorated function that retries on failure
    
    Example:
        from common.retry import retry_with_exponential_backoff
        from common.exceptions import OllamaConnectionError
        
        @retry_with_exponential_backoff(
            max_retries=5,
            exceptions=(OllamaConnectionError, ConnectionError)
        )
        def call_ollama_api():
            return llm.invoke("What is AI?")
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                
                except RateLimitError as e:
                    # Special handling for rate limit errors
                    last_exception = e
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries due to rate limiting"
                        )
                        raise
                    
                    # Use retry_after if provided, otherwise exponential backoff
                    wait_time = e.retry_after if e.retry_after else delay
                    wait_time = min(wait_time, max_delay)
                    
                    logger.warning(
                        f"{func.__name__} rate limited. Retry {attempt + 1}/{max_retries} "
                        f"after {wait_time:.2f}s"
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(wait_time)
                    delay *= exponential_base
                
                except exceptions as e:
                    last_exception = e
                    
                    if attempt >= max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {str(e)}"
                        )
                        raise
                    
                    # Apply max_delay cap before logging and sleeping
                    wait_time = min(delay, max_delay)
                    
                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {wait_time:.2f}s..."
                    )
                    
                    if on_retry:
                        on_retry(e, attempt + 1)
                    
                    time.sleep(wait_time)
                    delay = min(delay * exponential_base, max_delay)
            
            # Should not reach here, but just in case
            if last_exception:
                raise last_exception
        
        return wrapper
    return decorator


def retry_on_connection_error(max_retries: int = 3):
    """
    Convenience decorator for retrying on connection errors only.
    
    Retries on: ConnectionError, TimeoutError, OllamaConnectionError
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
    
    Example:
        @retry_on_connection_error(max_retries=5)
        def fetch_data():
            return requests.get("https://api.example.com/data")
    """
    from .exceptions import OllamaConnectionError
    
    return retry_with_exponential_backoff(
        max_retries=max_retries,
        exceptions=(ConnectionError, TimeoutError, OllamaConnectionError)
    )


def retry_on_rate_limit(max_retries: int = 5, initial_delay: float = 2.0):
    """
    Convenience decorator for retrying on rate limit errors with longer delays.
    
    Uses longer initial delay (2s) and allows more retries (5) since rate limits
    typically require backing off for longer periods.
    
    Args:
        max_retries: Maximum number of retry attempts (default: 5)
        initial_delay: Initial delay in seconds (default: 2.0)
    
    Example:
        @retry_on_rate_limit(max_retries=10)
        def call_rate_limited_api():
            return llm.invoke("Generate a story")
    """
    return retry_with_exponential_backoff(
        max_retries=max_retries,
        initial_delay=initial_delay,
        exceptions=(RateLimitError,)
    )
