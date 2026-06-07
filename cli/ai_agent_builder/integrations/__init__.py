"""
integrations/__init__.py — Integration module system initialization.
"""

from . import caching, observability, orchestration, vector_stores
from .base import IntegrationModule
from .registry import (
    get_integration,
    list_integrations,
    register_integration,
)

__all__ = [
    "IntegrationModule",
    "caching",
    "get_integration",
    "list_integrations",
    "observability",
    "orchestration",
    "register_integration",
    "vector_stores",
]
