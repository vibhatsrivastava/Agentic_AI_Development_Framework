"""
registry.py — Integration registry for discovering and accessing integrations.

Provides centralized registry of all available integrations with
discovery and lookup capabilities.
"""

from typing import Dict, List, Optional

from .base import IntegrationModule

# Global registry of available integrations
_INTEGRATION_REGISTRY: Dict[str, IntegrationModule] = {}


def register_integration(integration: IntegrationModule) -> None:
    """
    Register an integration module in the global registry.

    Args:
        integration: IntegrationModule instance to register

    Raises:
        ValueError: If integration with same name already registered
    """
    name = integration.name

    if name in _INTEGRATION_REGISTRY:
        raise ValueError(f"Integration '{name}' is already registered")

    _INTEGRATION_REGISTRY[name] = integration


def get_integration(name: str) -> Optional[IntegrationModule]:
    """
    Get an integration by name.

    Args:
        name: Integration name (e.g., 'pgvector', 'redis')

    Returns:
        IntegrationModule instance if found, None otherwise
    """
    return _INTEGRATION_REGISTRY.get(name)


def list_integrations(category: Optional[str] = None) -> List[IntegrationModule]:
    """
    List all registered integrations, optionally filtered by category.

    Args:
        category: Optional category filter ('vector_store', 'cache', 'observability', 'loader')

    Returns:
        List of IntegrationModule instances
    """
    integrations = list(_INTEGRATION_REGISTRY.values())

    if category:
        integrations = [i for i in integrations if i.category == category]

    # Sort by category then name
    integrations.sort(key=lambda i: (i.category, i.name))

    return integrations


def get_integration_names() -> List[str]:
    """
    Get list of all registered integration names.

    Returns:
        Sorted list of integration names
    """
    return sorted(_INTEGRATION_REGISTRY.keys())


def get_categories() -> List[str]:
    """
    Get list of all available categories.

    Returns:
        Sorted list of unique categories
    """
    categories = {integration.category for integration in _INTEGRATION_REGISTRY.values()}
    return sorted(categories)


def clear_registry() -> None:
    """Clear all registered integrations (for testing)."""
    _INTEGRATION_REGISTRY.clear()


# Import and register all built-in integrations
def _load_builtin_integrations() -> None:
    """
    Load and register all built-in integration modules.

    Import integration modules and register them in the global registry.
    This function is called at module import time.
    """
    # Vector stores
    from .vector_stores.chroma import ChromaIntegration
    from .vector_stores.faiss import FAISSIntegration
    from .vector_stores.pgvector import PgVectorIntegration
    register_integration(ChromaIntegration())
    register_integration(PgVectorIntegration())
    register_integration(FAISSIntegration())

    # Caching
    from .caching.redis import RedisIntegration
    register_integration(RedisIntegration())

    # Observability
    from .observability.langfuse import LangfuseIntegration
    register_integration(LangfuseIntegration())

    # Orchestration
    from .orchestration.awx import AwxIntegration
    register_integration(AwxIntegration())

    # Document loaders (future implementation)
    # from .loaders.pdf import PDFLoaderIntegration
    # from .loaders.web import WebScraperIntegration
    # register_integration(PDFLoaderIntegration())
    # register_integration(WebScraperIntegration())


# Auto-load integrations on import
_load_builtin_integrations()
