"""
exceptions.py — Custom exception classes for LangChain projects.

Provides standardized error types for common failure scenarios,
improving error handling consistency across all projects.
"""


class LangChainDevError(Exception):
    """Base exception class for all LangChain development project errors."""
    pass


class RateLimitError(LangChainDevError):
    """Raised when API rate limits are exceeded."""
    def __init__(self, message: str = "Rate limit exceeded", retry_after: float = None):
        self.retry_after = retry_after
        super().__init__(message)


class VaultError(LangChainDevError):
    """Raised when HashiCorp Vault operations fail."""
    pass


class VaultConnectionError(VaultError):
    """Raised when unable to connect to Vault server."""
    pass


class VaultAuthenticationError(VaultError):
    """Raised when Vault authentication fails."""
    pass


class VaultSecretNotFoundError(VaultError):
    """Raised when a requested secret doesn't exist in Vault."""
    def __init__(self, secret_path: str):
        self.secret_path = secret_path
        super().__init__(f"Secret not found at path: {secret_path}")


class OllamaConnectionError(LangChainDevError):
    """Raised when unable to connect to Ollama server."""
    pass


class OllamaModelNotFoundError(LangChainDevError):
    """Raised when requested Ollama model is not available."""
    def __init__(self, model_name: str):
        self.model_name = model_name
        super().__init__(f"Ollama model not found: {model_name}")


class TokenCountError(LangChainDevError):
    """Raised when token counting operations fail."""
    pass


class CacheError(LangChainDevError):
    """Raised when cache operations fail."""
    pass
