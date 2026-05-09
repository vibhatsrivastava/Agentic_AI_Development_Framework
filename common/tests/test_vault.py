"""
test_vault.py — Comprehensive tests for HashiCorp Vault integration
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
import logging

from common.vault import (
    get_secret,
    clear_cache,
    _get_vault_client,
    _fetch_from_vault,
    HVAC_AVAILABLE
)


@pytest.fixture(autouse=True)
def reset_vault_state():
    """Reset module-level state before each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def mock_env_vars():
    """Fixture to mock environment variables."""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def vault_enabled_env(mock_env_vars):
    """Environment with Vault enabled."""
    with patch.dict(os.environ, {
        "VAULT_ENABLED": "true",
        "VAULT_ADDR": "http://vault.example.com:8200",
        "VAULT_TOKEN": "test-token",
        "VAULT_SECRET_PATH": "ollama",
        "VAULT_MOUNT_POINT": "secret",
        "OLLAMA_API_KEY": "fallback-key-from-env"
    }):
        yield


@pytest.fixture
def vault_disabled_env(mock_env_vars):
    """Environment with Vault disabled."""
    with patch.dict(os.environ, {
        "VAULT_ENABLED": "false",
        "OLLAMA_API_KEY": "key-from-env-only"
    }):
        yield


class TestVaultDisabled:
    """Test behavior when Vault is disabled."""
    
    def test_vault_disabled_falls_back_to_env(self, vault_disabled_env):
        """When VAULT_ENABLED=false, should use .env without attempting Vault connection."""
        result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
        assert result == "key-from-env-only"
    
    def test_vault_disabled_returns_default_when_env_missing(self, vault_disabled_env):
        """When VAULT_ENABLED=false and env var missing, should return default."""
        result = get_secret("MISSING_KEY", "MISSING_KEY", default="default-value")
        assert result == "default-value"
    
    def test_vault_disabled_by_default(self, mock_env_vars):
        """Vault should be disabled by default when VAULT_ENABLED is not set."""
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "env-key"}):
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "env-key"


class TestVaultConfiguration:
    """Test Vault configuration validation."""
    
    def test_hvac_not_available(self, vault_enabled_env, caplog):
        """When hvac library is not installed, should fall back to .env."""
        with patch("common.vault.HVAC_AVAILABLE", False):
            caplog.set_level(logging.WARNING)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "hvac library is not installed" in caplog.text
    
    def test_vault_addr_missing(self, mock_env_vars, caplog):
        """When VAULT_ADDR is not set, should fall back to .env."""
        with patch.dict(os.environ, {
            "VAULT_ENABLED": "true",
            "VAULT_TOKEN": "test-token",
            "OLLAMA_API_KEY": "fallback-key"
        }):
            caplog.set_level(logging.WARNING)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key"
            assert "VAULT_ADDR is not set" in caplog.text
    
    def test_vault_token_missing(self, mock_env_vars, caplog):
        """When VAULT_TOKEN is not set, should fall back to .env."""
        with patch.dict(os.environ, {
            "VAULT_ENABLED": "true",
            "VAULT_ADDR": "http://vault.example.com:8200",
            "OLLAMA_API_KEY": "fallback-key"
        }):
            caplog.set_level(logging.WARNING)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key"
            assert "VAULT_TOKEN is not set" in caplog.text


class TestVaultAuthentication:
    """Test Vault authentication scenarios."""
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_authentication_failure(self, vault_enabled_env, caplog):
        """When Vault authentication fails, should fall back to .env."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = False
            mock_hvac.return_value = mock_client
            
            caplog.set_level(logging.ERROR)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "Vault authentication failed" in caplog.text
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_client_initialization_error(self, vault_enabled_env, caplog):
        """When Vault client initialization fails, should fall back to .env."""
        with patch("hvac.Client", side_effect=Exception("Connection refused")):
            caplog.set_level(logging.ERROR)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "Failed to initialize Vault client" in caplog.text


class TestVaultSecretRetrieval:
    """Test secret retrieval from Vault."""
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_successful_vault_retrieval(self, vault_enabled_env, caplog):
        """When Vault returns a secret, should use it instead of .env."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {
                    "data": {
                        "OLLAMA_API_KEY": "vault-secret-key"
                    }
                }
            }
            mock_hvac.return_value = mock_client
            
            caplog.set_level(logging.INFO)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "vault-secret-key"
            assert "Retrieved 'OLLAMA_API_KEY' from Vault" in caplog.text
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_secret_not_found(self, vault_enabled_env, caplog):
        """When secret key not found in Vault, should fall back to .env."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {
                    "data": {
                        "OTHER_KEY": "other-value"
                    }
                }
            }
            mock_hvac.return_value = mock_client
            
            caplog.set_level(logging.WARNING)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "Key 'OLLAMA_API_KEY' not found in Vault secret" in caplog.text
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_path_does_not_exist(self, vault_enabled_env, caplog):
        """When Vault secret path does not exist, should fall back to .env."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            
            # Simulate InvalidPath exception
            import hvac.exceptions
            mock_client.secrets.kv.v2.read_secret_version.side_effect = hvac.exceptions.InvalidPath()
            mock_hvac.return_value = mock_client
            
            caplog.set_level(logging.WARNING)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "Vault secret path" in caplog.text
            assert "does not exist" in caplog.text
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_permission_denied(self, vault_enabled_env, caplog):
        """When Vault returns Forbidden, should fall back to .env."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            
            import hvac.exceptions
            mock_client.secrets.kv.v2.read_secret_version.side_effect = hvac.exceptions.Forbidden()
            mock_hvac.return_value = mock_client
            
            caplog.set_level(logging.ERROR)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "Permission denied" in caplog.text
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_generic_error(self, vault_enabled_env, caplog):
        """When Vault raises generic error, should fall back to .env."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Network timeout")
            mock_hvac.return_value = mock_client
            
            caplog.set_level(logging.ERROR)
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "fallback-key-from-env"
            assert "Error fetching secret from Vault" in caplog.text


class TestSecretCaching:
    """Test secret caching behavior."""
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_cache_prevents_duplicate_vault_calls(self, vault_enabled_env, caplog):
        """Repeated calls should use cache, not hit Vault again."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            mock_client.secrets.kv.v2.read_secret_version.return_value = {
                "data": {
                    "data": {
                        "OLLAMA_API_KEY": "vault-cached-key"
                    }
                }
            }
            mock_hvac.return_value = mock_client
            
            # First call - should hit Vault
            result1 = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result1 == "vault-cached-key"
            assert mock_client.secrets.kv.v2.read_secret_version.call_count == 1
            
            # Second call - should use cache
            caplog.clear()
            caplog.set_level(logging.DEBUG)
            result2 = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result2 == "vault-cached-key"
            assert mock_client.secrets.kv.v2.read_secret_version.call_count == 1  # Not called again
            assert "Using cached value" in caplog.text
    
    def test_clear_cache_forces_refresh(self, vault_disabled_env):
        """clear_cache() should force re-fetching secrets."""
        # First call
        result1 = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
        assert result1 == "key-from-env-only"
        
        # Change env var
        with patch.dict(os.environ, {"OLLAMA_API_KEY": "new-key-from-env"}):
            # Without clear_cache, should still get cached value
            result2 = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result2 == "key-from-env-only"  # Cached
            
            # After clear_cache, should get new value
            clear_cache()
            result3 = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result3 == "new-key-from-env"  # Fresh


class TestDefaultValues:
    """Test default value handling."""
    
    def test_custom_default_used_when_secret_missing(self, vault_disabled_env):
        """When secret not in Vault or .env, should return custom default."""
        result = get_secret("NONEXISTENT_KEY", "NONEXISTENT_KEY", default="custom-default")
        assert result == "custom-default"
    
    def test_empty_string_default(self, vault_disabled_env):
        """Default value of empty string should work."""
        result = get_secret("NONEXISTENT_KEY", "NONEXISTENT_KEY", default="")
        assert result == ""
    
    def test_env_value_preferred_over_default(self, vault_disabled_env):
        """If .env has value, should use it instead of default."""
        with patch.dict(os.environ, {"MY_KEY": "env-value"}):
            result = get_secret("MY_KEY", "MY_KEY", default="default-value")
            assert result == "env-value"


class TestVaultClientSingleton:
    """Test Vault client singleton behavior."""
    
    @pytest.mark.skipif(not HVAC_AVAILABLE, reason="hvac library not installed")
    def test_vault_client_initialized_once(self, vault_enabled_env):
        """Vault client should be initialized once and reused."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            mock_hvac.return_value = mock_client
            
            # Call _get_vault_client multiple times
            client1 = _get_vault_client()
            client2 = _get_vault_client()
            
            assert client1 is client2
            assert mock_hvac.call_count == 1  # Created only once
    
    def test_clear_cache_resets_client(self, vault_enabled_env):
        """clear_cache() should reset the Vault client singleton."""
        with patch("hvac.Client") as mock_hvac:
            mock_client = Mock()
            mock_client.is_authenticated.return_value = True
            mock_hvac.return_value = mock_client
            
            # Get client
            client1 = _get_vault_client()
            assert mock_hvac.call_count == 1
            
            # Clear cache
            clear_cache()
            
            # Get client again - should reinitialize
            client2 = _get_vault_client()
            assert mock_hvac.call_count == 2


class TestVaultEnabledVariants:
    """Test various ways to set VAULT_ENABLED."""
    
    @pytest.mark.parametrize("enabled_value", ["true", "True", "TRUE", "1", "yes", "Yes"])
    def test_vault_enabled_truthy_values(self, mock_env_vars, enabled_value):
        """Various truthy values should enable Vault."""
        with patch.dict(os.environ, {
            "VAULT_ENABLED": enabled_value,
            "VAULT_ADDR": "http://vault.example.com:8200",
            "VAULT_TOKEN": "test-token",
            "OLLAMA_API_KEY": "env-fallback"
        }):
            with patch("hvac.Client") as mock_hvac:
                mock_client = Mock()
                mock_client.is_authenticated.return_value = True
                mock_client.secrets.kv.v2.read_secret_version.return_value = {
                    "data": {"data": {"OLLAMA_API_KEY": "vault-key"}}
                }
                mock_hvac.return_value = mock_client
                
                result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
                assert result == "vault-key"
    
    @pytest.mark.parametrize("disabled_value", ["false", "False", "FALSE", "0", "no", ""])
    def test_vault_disabled_falsy_values(self, mock_env_vars, disabled_value):
        """Various falsy values should disable Vault."""
        with patch.dict(os.environ, {
            "VAULT_ENABLED": disabled_value,
            "OLLAMA_API_KEY": "env-only"
        }):
            result = get_secret("OLLAMA_API_KEY", "OLLAMA_API_KEY")
            assert result == "env-only"
