"""
test_exceptions.py — Tests for common.exceptions module.
"""

import pytest
from common.exceptions import (
    LangChainDevError,
    RateLimitError,
    VaultError,
    VaultConnectionError,
    VaultAuthenticationError,
    VaultSecretNotFoundError,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    TokenCountError,
    CacheError
)


class TestCustomExceptions:
    """Test suite for custom exception classes."""
    
    def test_base_exception(self):
        """Test base LangChainDevError exception."""
        error = LangChainDevError("test error")
        assert str(error) == "test error"
        assert isinstance(error, Exception)
    
    def test_rate_limit_error_basic(self):
        """Test RateLimitError without retry_after."""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after is None
    
    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry_after parameter."""
        error = RateLimitError("Rate limit exceeded", retry_after=5.0)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 5.0
    
    def test_vault_error(self):
        """Test VaultError exception."""
        error = VaultError("Vault operation failed")
        assert str(error) == "Vault operation failed"
        assert isinstance(error, LangChainDevError)
    
    def test_vault_connection_error(self):
        """Test VaultConnectionError exception."""
        error = VaultConnectionError("Cannot connect to Vault")
        assert str(error) == "Cannot connect to Vault"
        assert isinstance(error, VaultError)
    
    def test_vault_authentication_error(self):
        """Test VaultAuthenticationError exception."""
        error = VaultAuthenticationError("Authentication failed")
        assert str(error) == "Authentication failed"
        assert isinstance(error, VaultError)
    
    def test_vault_secret_not_found_error(self):
        """Test VaultSecretNotFoundError with secret path."""
        error = VaultSecretNotFoundError("secret/data/myapp")
        assert "secret/data/myapp" in str(error)
        assert error.secret_path == "secret/data/myapp"
        assert isinstance(error, VaultError)
    
    def test_ollama_connection_error(self):
        """Test OllamaConnectionError exception."""
        error = OllamaConnectionError("Cannot connect to Ollama")
        assert str(error) == "Cannot connect to Ollama"
        assert isinstance(error, LangChainDevError)
    
    def test_ollama_model_not_found_error(self):
        """Test OllamaModelNotFoundError with model name."""
        error = OllamaModelNotFoundError("llama3.1:8b")
        assert "llama3.1:8b" in str(error)
        assert error.model_name == "llama3.1:8b"
        assert isinstance(error, LangChainDevError)
    
    def test_token_count_error(self):
        """Test TokenCountError exception."""
        error = TokenCountError("Token counting failed")
        assert str(error) == "Token counting failed"
        assert isinstance(error, LangChainDevError)
    
    def test_cache_error(self):
        """Test CacheError exception."""
        error = CacheError("Cache operation failed")
        assert str(error) == "Cache operation failed"
        assert isinstance(error, LangChainDevError)
    
    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from LangChainDevError."""
        exceptions_to_test = [
            RateLimitError(),
            VaultError(),
            VaultConnectionError(),
            VaultAuthenticationError(),
            VaultSecretNotFoundError("path"),
            OllamaConnectionError(),
            OllamaModelNotFoundError("model"),
            TokenCountError(),
            CacheError()
        ]
        
        for exc in exceptions_to_test:
            assert isinstance(exc, LangChainDevError)
            assert isinstance(exc, Exception)
