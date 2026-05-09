"""
test_cache.py — Tests for common.cache.in_memory module.
"""

import pytest
import time
import threading
from common.cache.in_memory import LRUCache, get_global_cache
from common.exceptions import CacheError


class TestLRUCache:
    """Test suite for LRUCache class."""
    
    def test_initialize_cache(self):
        """Test cache initialization."""
        cache = LRUCache(capacity=10, ttl=60)
        
        assert cache.capacity == 10
        assert cache.ttl == 60
        assert cache.size() == 0
    
    def test_initialize_cache_invalid_capacity(self):
        """Test that invalid capacity raises error."""
        with pytest.raises(CacheError, match="capacity must be positive"):
            LRUCache(capacity=0)
        
        with pytest.raises(CacheError, match="capacity must be positive"):
            LRUCache(capacity=-5)
    
    def test_put_and_get(self):
        """Test basic put and get operations."""
        cache = LRUCache(capacity=10)
        
        cache.put("key1", "value1")
        result = cache.get("key1")
        
        assert result == "value1"
        assert cache.size() == 1
    
    def test_get_nonexistent_key(self):
        """Test getting a key that doesn't exist."""
        cache = LRUCache(capacity=10)
        
        result = cache.get("nonexistent")
        
        assert result is None
    
    def test_put_updates_existing_key(self):
        """Test that putting an existing key updates the value."""
        cache = LRUCache(capacity=10)
        
        cache.put("key1", "value1")
        cache.put("key1", "updated_value")
        
        result = cache.get("key1")
        
        assert result == "updated_value"
        assert cache.size() == 1  # Still only one entry
    
    def test_lru_eviction(self):
        """Test that least recently used items are evicted."""
        cache = LRUCache(capacity=3)
        
        # Fill cache
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Access key1 to make it recently used
        cache.get("key1")
        
        # Add new item - should evict key2 (least recently used)
        cache.put("key4", "value4")
        
        assert cache.get("key1") == "value1"  # Still present
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # Still present
        assert cache.get("key4") == "value4"  # Newly added
        assert cache.size() == 3
    
    def test_ttl_expiration(self):
        """Test that entries expire after TTL."""
        cache = LRUCache(capacity=10, ttl=0.1)  # 0.1 second TTL
        
        cache.put("key1", "value1")
        
        # Should be available immediately
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(0.15)
        
        # Should be expired now
        assert cache.get("key1") is None
    
    def test_no_ttl_expiration(self):
        """Test that entries don't expire when TTL is None."""
        cache = LRUCache(capacity=10, ttl=None)
        
        cache.put("key1", "value1")
        
        # Wait some time
        time.sleep(0.1)
        
        # Should still be available
        assert cache.get("key1") == "value1"
    
    def test_delete_existing_key(self):
        """Test deleting an existing key."""
        cache = LRUCache(capacity=10)
        
        cache.put("key1", "value1")
        result = cache.delete("key1")
        
        assert result is True
        assert cache.get("key1") is None
        assert cache.size() == 0
    
    def test_delete_nonexistent_key(self):
        """Test deleting a key that doesn't exist."""
        cache = LRUCache(capacity=10)
        
        result = cache.delete("nonexistent")
        
        assert result is False
    
    def test_clear(self):
        """Test clearing all entries."""
        cache = LRUCache(capacity=10)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        cache.clear()
        
        assert cache.size() == 0
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
    
    def test_get_stats_empty_cache(self):
        """Test getting stats for empty cache."""
        cache = LRUCache(capacity=10)
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["hit_rate"] == "0.00%"
        assert stats["evictions"] == 0
        assert stats["size"] == 0
        assert stats["capacity"] == 10
    
    def test_get_stats_with_hits_and_misses(self):
        """Test cache statistics with hits and misses."""
        cache = LRUCache(capacity=10)
        
        cache.put("key1", "value1")
        
        # 2 hits
        cache.get("key1")
        cache.get("key1")
        
        # 3 misses
        cache.get("key2")
        cache.get("key3")
        cache.get("key4")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 2
        assert stats["misses"] == 3
        assert stats["hit_rate"] == "40.00%"  # 2/5 * 100
        assert stats["size"] == 1
    
    def test_get_stats_with_evictions(self):
        """Test cache statistics with evictions."""
        cache = LRUCache(capacity=2)
        
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")  # Evicts key1
        cache.put("key4", "value4")  # Evicts key2
        
        stats = cache.get_stats()
        
        assert stats["evictions"] == 2
        assert stats["size"] == 2
    
    def test_reset_stats(self):
        """Test resetting cache statistics."""
        cache = LRUCache(capacity=10)
        
        cache.put("key1", "value1")
        cache.get("key1")  # Hit
        cache.get("key2")  # Miss
        
        cache.reset_stats()
        
        stats = cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["evictions"] == 0
    
    def test_thread_safety(self):
        """Test that cache is thread-safe."""
        cache = LRUCache(capacity=100)
        errors = []
        
        def put_items(start, end):
            try:
                for i in range(start, end):
                    cache.put(f"key{i}", f"value{i}")
            except Exception as e:
                errors.append(e)
        
        def get_items(start, end):
            try:
                for i in range(start, end):
                    cache.get(f"key{i}")
            except Exception as e:
                errors.append(e)
        
        # Create multiple threads doing concurrent operations
        threads = []
        threads.append(threading.Thread(target=put_items, args=(0, 50)))
        threads.append(threading.Thread(target=put_items, args=(50, 100)))
        threads.append(threading.Thread(target=get_items, args=(0, 50)))
        threads.append(threading.Thread(target=get_items, args=(50, 100)))
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # No errors should occur
        assert len(errors) == 0
        assert cache.size() <= 100
    
    def test_cache_with_complex_values(self):
        """Test caching complex objects."""
        cache = LRUCache(capacity=10)
        
        # Cache different types of objects
        cache.put("int", 42)
        cache.put("list", [1, 2, 3])
        cache.put("dict", {"key": "value"})
        cache.put("tuple", (1, 2, 3))
        
        assert cache.get("int") == 42
        assert cache.get("list") == [1, 2, 3]
        assert cache.get("dict") == {"key": "value"}
        assert cache.get("tuple") == (1, 2, 3)


class TestGlobalCache:
    """Test suite for global cache functions."""
    
    def test_get_global_cache(self):
        """Test getting global cache instance."""
        cache = get_global_cache()
        
        assert cache is not None
        assert isinstance(cache, LRUCache)
        assert cache.capacity == 100
        assert cache.ttl == 3600
    
    def test_get_global_cache_singleton(self):
        """Test that get_global_cache returns same instance."""
        cache1 = get_global_cache()
        cache2 = get_global_cache()
        
        assert cache1 is cache2
    
    def test_get_global_cache_persists_data(self):
        """Test that global cache persists data across calls."""
        cache1 = get_global_cache()
        cache1.put("test_key", "test_value")
        
        cache2 = get_global_cache()
        result = cache2.get("test_key")
        
        assert result == "test_value"
        
        # Clean up
        cache1.clear()
