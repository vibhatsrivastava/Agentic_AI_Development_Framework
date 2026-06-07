"""
Tests for common/langfuse_tracing.py — Langfuse callback handler initialization.

Covers:
- Handler initialization when enabled with valid keys
- Handler returns None when disabled
- Handler returns None when keys are missing
- Handler returns None when ImportError occurs
- Vault integration support
- Caching behavior (handler initialized once per process)
"""

from unittest.mock import Mock, patch


def test_get_callback_handler_enabled_with_keys(monkeypatch, mock_langfuse):
    """Test handler is created when enabled with valid keys."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    # Reset state for clean test
    reset_handler()
    
    # Configure environment
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test-123")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test-456")
    monkeypatch.setenv("LANGFUSE_HOST", "http://test-langfuse:3000")
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    
    # Mock Langfuse client class (initialized first in Langfuse 4.x)
    mock_langfuse_client = Mock()
    mock_langfuse_module = Mock()
    mock_langfuse_module.Langfuse = mock_langfuse_client
    
    sys.modules['langfuse'] = mock_langfuse_module
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        # Mock get_secret to return env vars (simulating .env fallback)
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-test-123",
                "LANGFUSE_SECRET_KEY": "sk-test-456",
            }.get(vault_key, default)
            
            handler = get_langfuse_callback_handler()
        
        # Verify handler was created
        assert handler is not None
        
        # In Langfuse 4.x, global client is initialized first with keys
        mock_langfuse_client.assert_called_once_with(
            public_key="pk-test-123",
            secret_key="sk-test-456",
            host="http://test-langfuse:3000",
        )
        
        # Then CallbackHandler is created with no arguments (uses global client)
        mock_handler_class.assert_called_once_with()
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_disabled(monkeypatch):
    """Test handler returns None when LANGFUSE_ENABLED=false."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    
    handler = get_langfuse_callback_handler()
    
    assert handler is None


def test_get_callback_handler_missing_public_key(monkeypatch, mock_langfuse):
    """Test handler returns None when public key is missing."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    sys.modules['langfuse'] = Mock()
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        # Mock get_secret to return empty for public key
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "",  # Missing
                "LANGFUSE_SECRET_KEY": "sk-test-456",
            }.get(vault_key, default)
            
            handler = get_langfuse_callback_handler()
        
        assert handler is None
        mock_handler_class.assert_not_called()
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_missing_secret_key(monkeypatch, mock_langfuse):
    """Test handler returns None when secret key is missing."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    sys.modules['langfuse'] = Mock()
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        # Mock get_secret to return empty for secret key
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-test-123",
                "LANGFUSE_SECRET_KEY": "",  # Missing
            }.get(vault_key, default)
            
            handler = get_langfuse_callback_handler()
        
        assert handler is None
        mock_handler_class.assert_not_called()
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_import_error(monkeypatch):
    """Test handler returns None when langfuse library is not installed."""
    from common.langfuse_tracing import reset_handler
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    
    # Ensure sys.modules is clean (no mock modules from other tests)
    import sys
    sys.modules.pop('langfuse', None)
    sys.modules.pop('langfuse.langchain', None)
    
    # Mock ImportError for langfuse.langchain
    with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
        mock_get_secret.return_value = "test-key"
        
        # Simulate ImportError by patching the import
        import builtins
        original_import = builtins.__import__
        
        def mock_import(name, *args, **kwargs):
            if name == "langfuse.langchain" or name == "langfuse":
                raise ImportError("No module named 'langfuse'")
            return original_import(name, *args, **kwargs)
        
        with patch("builtins.__import__", side_effect=mock_import):
            # Re-import to trigger ImportError
            import importlib
            import common.langfuse_tracing
            importlib.reload(common.langfuse_tracing)
            
            handler = common.langfuse_tracing.get_langfuse_callback_handler()
            
            assert handler is None


def test_get_callback_handler_caching(monkeypatch, mock_langfuse):
    """Test handler is cached and not re-initialized on subsequent calls."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-test")
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    sys.modules['langfuse'] = Mock()
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
            }.get(vault_key, default)
            
            # First call - initializes handler
            handler1 = get_langfuse_callback_handler()
            
            # Second call - returns cached handler
            handler2 = get_langfuse_callback_handler()
        
        # Verify same handler returned
        assert handler1 is handler2
        
        # Verify CallbackHandler was only instantiated once
        assert mock_handler_class.call_count == 1
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_vault_integration(monkeypatch, mock_langfuse):
    """Test handler fetches keys from Vault when Vault is enabled."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("VAULT_ENABLED", "true")
    # Clear any existing LANGFUSE_HOST to use default
    monkeypatch.delenv("LANGFUSE_HOST", raising=False)
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    
    # Mock Langfuse client class (initialized first in Langfuse 4.x)
    mock_langfuse_client = Mock()
    mock_langfuse_module = Mock()
    mock_langfuse_module.Langfuse = mock_langfuse_client
    
    sys.modules['langfuse'] = mock_langfuse_module
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        # Mock get_secret to simulate Vault response
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-from-vault",
                "LANGFUSE_SECRET_KEY": "sk-from-vault",
            }.get(vault_key, default)
            
            handler = get_langfuse_callback_handler()
            
            # Verify get_secret was called with vault_path="langfuse"
            assert mock_get_secret.call_count == 2
            
            # Check that vault_path was passed correctly
            calls = mock_get_secret.call_args_list
            assert calls[0][1]["vault_path"] == "langfuse"  # public key call
            assert calls[1][1]["vault_path"] == "langfuse"  # secret key call
        
        # Verify handler was created with Vault keys
        assert handler is not None
        
        # In Langfuse 4.x, global client is initialized first with keys
        mock_langfuse_client.assert_called_once_with(
            public_key="pk-from-vault",
            secret_key="sk-from-vault",
            host="https://cloud.langfuse.com",  # default host
        )
        
        # Then CallbackHandler is created with no arguments (uses global client)
        mock_handler_class.assert_called_once_with()
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_custom_host(monkeypatch, mock_langfuse):
    """Test handler uses custom LANGFUSE_HOST if provided."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    monkeypatch.setenv("LANGFUSE_HOST", "http://custom-host:9000")
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    
    # Mock Langfuse client class (initialized first in Langfuse 4.x)
    mock_langfuse_client = Mock()
    mock_langfuse_module = Mock()
    mock_langfuse_module.Langfuse = mock_langfuse_client
    
    sys.modules['langfuse'] = mock_langfuse_module
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
            }.get(vault_key, default)

            get_langfuse_callback_handler()

        # In Langfuse 4.x, global client is initialized first with keys
        mock_langfuse_client.assert_called_once_with(
            public_key="pk-test",
            secret_key="sk-test",
            host="http://custom-host:9000",
        )
        
        # Then CallbackHandler is created with no arguments (uses global client)
        mock_handler_class.assert_called_once_with()
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_initialization_error(monkeypatch, mock_langfuse):
    """Test handler returns None when CallbackHandler initialization fails."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    reset_handler()
    monkeypatch.setenv("LANGFUSE_ENABLED", "true")
    
    # Make CallbackHandler raise an exception
    mock_handler_class.side_effect = Exception("Connection failed")
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    sys.modules['langfuse'] = Mock()
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
            }.get(vault_key, default)
            
            handler = get_langfuse_callback_handler()
        
        assert handler is None
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_reset_handler():
    """Test reset_handler clears cached handler for re-initialization."""
    import common.langfuse_tracing
    from common.langfuse_tracing import reset_handler

    reset_handler()

    # Verify internal state is reset
    assert common.langfuse_tracing._CALLBACK_HANDLER is None
    assert common.langfuse_tracing._INITIALIZATION_ATTEMPTED is False


def test_get_callback_handler_enabled_variants(monkeypatch, mock_langfuse):
    """Test various truthy values for LANGFUSE_ENABLED."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    mock_handler_class, mock_handler_instance = mock_langfuse
    
    # Mock langfuse.langchain module in sys.modules
    import sys
    mock_callback_module = Mock()
    mock_callback_module.CallbackHandler = mock_handler_class
    sys.modules['langfuse'] = Mock()
    sys.modules['langfuse.langchain'] = mock_callback_module
    
    try:
        with patch("common.langfuse_tracing.get_secret") as mock_get_secret:
            mock_get_secret.side_effect = lambda vault_key, env_fallback_key, default="", vault_path=None: {
                "LANGFUSE_PUBLIC_KEY": "pk-test",
                "LANGFUSE_SECRET_KEY": "sk-test",
            }.get(vault_key, default)
            
            for enabled_value in ["true", "True", "TRUE", "1", "yes", "Yes", "YES"]:
                reset_handler()
                monkeypatch.setenv("LANGFUSE_ENABLED", enabled_value)
                
                handler = get_langfuse_callback_handler()
                assert handler is not None, f"Failed for LANGFUSE_ENABLED={enabled_value}"
    finally:
        # Clean up sys.modules
        sys.modules.pop('langfuse.langchain', None)
        sys.modules.pop('langfuse', None)


def test_get_callback_handler_disabled_variants(monkeypatch):
    """Test various falsy values for LANGFUSE_ENABLED."""
    from common.langfuse_tracing import get_langfuse_callback_handler, reset_handler
    
    for disabled_value in ["false", "False", "FALSE", "0", "no", "No", "NO"]:
        reset_handler()
        monkeypatch.setenv("LANGFUSE_ENABLED", disabled_value)
        
        handler = get_langfuse_callback_handler()
        assert handler is None, f"Failed for LANGFUSE_ENABLED={disabled_value}"

