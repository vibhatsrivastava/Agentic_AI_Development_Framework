"""
integrations/__init__.py — Integration module system initialization.
"""

from .base import IntegrationModule
from .registry import get_integration, list_integrations, register_integration

__all__ = [
    "IntegrationModule",
    "get_integration",
    "list_integrations",
    "register_integration",
]
