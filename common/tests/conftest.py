"""
Common package-specific pytest fixtures.

Shared fixtures (mock_llm, mock_chat_llm, mock_embeddings, mock_env) are defined
in the root-level conftest.py and are automatically available to all tests.

This file can contain fixtures specific to common/ package tests only.
"""

# All shared fixtures are now in the root conftest.py
# They are automatically available to these tests via pytest's fixture discovery
