"""
AI Agent Builder — CLI for scaffolding AI Agent projects with composable integrations.

A development SDK that automates project scaffolding, provides built-in production foundations
(rate limiting, retry logic, token counting), and supports composable integration modules
(vector stores, caching, observability).
"""

__version__ = "0.1.0"
__author__ = "AI Agent Builder Team"
__description__ = "CLI tool for scaffolding production-ready AI Agent projects"

from .version import get_version

__all__ = ["__version__", "get_version"]
