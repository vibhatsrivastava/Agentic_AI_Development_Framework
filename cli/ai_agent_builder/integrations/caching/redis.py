"""
redis.py — Redis caching integration module.

Industry-standard caching for LLM responses, rate limiting, and session storage.
"""

from typing import Dict, List, Optional, Tuple

from ..base import IntegrationModule


class RedisIntegration(IntegrationModule):
    """
    Redis integration for caching LLM responses.

    Provides distributed caching with TTL support.
    """

    @property
    def name(self) -> str:
        return "redis"

    @property
    def display_name(self) -> str:
        return "Redis"

    @property
    def description(self) -> str:
        return "In-memory caching for LLM responses and rate limiting"

    @property
    def category(self) -> str:
        return "cache"

    def get_dependencies(self) -> List[str]:
        return [
            "redis>=5.0.0",
            "langchain-redis>=0.1.0",
        ]

    def get_env_vars(self) -> Dict[str, str]:
        return {
            "REDIS_HOST": "localhost",
            "REDIS_PORT": "6379",
            "REDIS_DB": "0",
            "REDIS_PASSWORD": "",
            "REDIS_TTL": "3600",  # 1 hour default TTL
        }

    def get_template_files(self) -> List[Tuple[str, str]]:
        return [
            ("redis/cache.py.j2", "src/cache/redis_cache.py"),
        ]

    def get_test_fixtures(self) -> str:
        return '''
@pytest.fixture
def mock_redis_client(mocker):
    """Mock Redis client for testing."""
    mock_client = mocker.Mock()
    mock_client.get.return_value = None
    mock_client.set.return_value = True
    mock_client.delete.return_value = 1
    mock_client.ping.return_value = True
    mocker.patch("redis.Redis", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_redis_cache(mocker):
    """Mock Redis cache for testing."""
    from langchain_redis import RedisCache

    mock_cache = mocker.Mock(spec=RedisCache)
    mock_cache.lookup.return_value = None
    mock_cache.update.return_value = None
    return mock_cache
'''

    def get_prerequisites(self) -> List[str]:
        return [
            "Redis server installed and running",
            "Redis accessible at configured host:port",
            "Optional: Redis password configured for secure connections",
        ]

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """Check if Redis is installed."""
        try:
            import redis  # noqa: F401
            return (True, None)
        except ImportError:
            return (False, "redis not installed. Run: pip install redis")
