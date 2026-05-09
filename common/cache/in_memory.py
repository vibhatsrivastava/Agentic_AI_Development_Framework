"""
in_memory.py — LRU cache implementation for simple projects.

Provides a thread-safe Least Recently Used (LRU) cache for caching
LLM responses, embeddings, or other expensive computations.
"""

import time
import threading
from typing import Any, Optional, Dict, Tuple
from collections import OrderedDict
from ..exceptions import CacheError
from ..utils import get_logger

logger = get_logger(__name__)


class LRUCache:
    """
    Thread-safe Least Recently Used (LRU) cache with TTL support.
    
    Features:
    - Automatic eviction of least recently used items when capacity is reached
    - Optional time-to-live (TTL) for cache entries
    - Thread-safe operations
    - Hit/miss statistics
    
    Args:
        capacity: Maximum number of items to store (default: 100)
        ttl: Time-to-live for cache entries in seconds (None = no expiration)
    
    Example:
        # Cache LLM responses
        cache = LRUCache(capacity=50, ttl=3600)  # 1 hour TTL
        
        # Check cache before LLM call
        response = cache.get(prompt)
        if response is None:
            response = llm.invoke(prompt)
            cache.put(prompt, response)
    """
    
    def __init__(self, capacity: int = 100, ttl: Optional[float] = None):
        """
        Initialize the LRU cache.
        
        Args:
            capacity: Maximum number of items (default: 100)
            ttl: Time-to-live in seconds (None = no expiration)
        """
        if capacity <= 0:
            raise CacheError("Cache capacity must be positive")
        
        self.capacity = capacity
        self.ttl = ttl
        self.cache: OrderedDict[str, Tuple[Any, float]] = OrderedDict()
        self.lock = threading.Lock()
        
        # Statistics
        self.hits = 0
        self.misses = 0
        self.evictions = 0
        
        logger.debug(f"LRU cache initialized: capacity={capacity}, ttl={ttl}")
    
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value if found and not expired, None otherwise
        """
        with self.lock:
            if key not in self.cache:
                self.misses += 1
                logger.debug(f"Cache miss: {key}")
                return None
            
            value, timestamp = self.cache[key]
            
            # Check TTL expiration
            if self.ttl is not None:
                age = time.time() - timestamp
                if age > self.ttl:
                    # Entry expired
                    del self.cache[key]
                    self.misses += 1
                    logger.debug(f"Cache miss (expired): {key}, age={age:.2f}s")
                    return None
            
            # Move to end (mark as recently used)
            self.cache.move_to_end(key)
            self.hits += 1
            logger.debug(f"Cache hit: {key}")
            return value
    
    def put(self, key: str, value: Any) -> None:
        """
        Store a value in the cache.
        
        Args:
            key: Cache key
            value: Value to store
        """
        with self.lock:
            timestamp = time.time()
            
            if key in self.cache:
                # Update existing entry
                del self.cache[key]
            elif len(self.cache) >= self.capacity:
                # Evict least recently used item
                evicted_key, _ = self.cache.popitem(last=False)
                self.evictions += 1
                logger.debug(f"Cache eviction: {evicted_key}")
            
            # Add new entry
            self.cache[key] = (value, timestamp)
            logger.debug(f"Cache put: {key}")
    
    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.
        
        Args:
            key: Cache key to remove
        
        Returns:
            True if key was found and removed, False otherwise
        """
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                logger.debug(f"Cache delete: {key}")
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries from the cache."""
        with self.lock:
            count = len(self.cache)
            self.cache.clear()
            logger.info(f"Cache cleared: {count} entries removed")
    
    def size(self) -> int:
        """
        Get the current number of entries in the cache.
        
        Returns:
            Number of cached entries
        """
        with self.lock:
            return len(self.cache)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dict with hits, misses, hit_rate, evictions, size
        """
        with self.lock:
            total_requests = self.hits + self.misses
            hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0.0
            
            return {
                "hits": self.hits,
                "misses": self.misses,
                "hit_rate": f"{hit_rate:.2f}%",
                "evictions": self.evictions,
                "size": len(self.cache),
                "capacity": self.capacity
            }
    
    def reset_stats(self) -> None:
        """Reset cache statistics (hits, misses, evictions)."""
        with self.lock:
            self.hits = 0
            self.misses = 0
            self.evictions = 0
            logger.debug("Cache statistics reset")


# Global cache instance for convenience
_global_cache: Optional[LRUCache] = None


def get_global_cache(capacity: int = 100, ttl: Optional[float] = 3600) -> LRUCache:
    """
    Get the global LRU cache instance.
    
    Creates a default cache on first use:
    - Capacity: 100 entries
    - TTL: 1 hour (3600 seconds)
    
    Args:
        capacity: Cache capacity (only used on first call)
        ttl: Time-to-live in seconds (only used on first call)
    
    Returns:
        Global LRUCache instance
    
    Example:
        from common.cache import get_global_cache
        
        cache = get_global_cache()
        
        # Check cache before expensive operation
        result = cache.get(key)
        if result is None:
            result = expensive_operation()
            cache.put(key, result)
    """
    global _global_cache
    
    if _global_cache is None:
        _global_cache = LRUCache(capacity=capacity, ttl=ttl)
        logger.info(f"Global cache created: capacity={capacity}, ttl={ttl}s")
    
    return _global_cache
