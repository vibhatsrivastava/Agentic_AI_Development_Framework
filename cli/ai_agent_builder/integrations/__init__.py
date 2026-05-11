"""
integrations/__init__.py — Integration module system initialization.
"""

from .base import IntegrationModule
from .registry import get_integration, list_integrations, register_integration

# Import integration modules to trigger registration
from . import caching
from . import observability
from . import orchestration  # AWX integration
from . import vector_stores

__all__ = [
    "IntegrationModule",
    "get_integration",
    "list_integrations",
    "register_integration",
]
