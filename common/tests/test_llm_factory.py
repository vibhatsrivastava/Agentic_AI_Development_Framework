"""
test_llm_factory.py — Comprehensive tests for common/llm_factory.py

Tests cover:
- get_llm() returns configured OllamaLLM instances
- get_chat_llm() returns configured ChatOllama instances
- get_embeddings() returns configured OllamaEmbeddings instances
- Model and parameter overrides work correctly
- Default values from environment variables are used
- Factory functions handle various parameter combinations

Coverage target: >= 90%
"""
import sys
import os

# Add repo root to Python path to enable imports from common/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
import pytest
from unittest.mock import patch, Mock, call
from common.llm_factory import get_llm, get_chat_llm, get_embeddings


@pytest.mark.unit
class TestGetLLM:
    """Unit tests for get_llm()."""
    
    @patch("common.llm_factory.OllamaLLM")
    def test_returns_ollama_llm_instance(self, mock_class):
        """get_llm() returns an OllamaLLM instance."""
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        
        llm = get_llm()
        
        mock_class.assert_called_once()
        assert llm == mock_instance
    
    @patch("common.llm_factory.OllamaLLM")
    def test_uses_default_model_from_env(self, mock_class, monkeypatch):
        """get_llm() uses OLLAMA_MODEL from environment."""
        monkeypatch.setenv("OLLAMA_MODEL", "test-model:latest")
        # Reload the module constants by directly patching _DEFAULT_MODEL
        with patch("common.llm_factory._DEFAULT_MODEL", "test-model:latest"):
            get_llm()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["model"] == "test-model:latest"
    
    @patch("common.llm_factory.OllamaLLM")
    def test_model_override_works(self, mock_class):
        """get_llm(model='custom') overrides default model."""
        get_llm(model="custom-model:7b")
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "custom-model:7b"
    
    @patch("common.llm_factory.OllamaLLM")
    def test_temperature_parameter_default(self, mock_class):
        """get_llm() uses temperature=0.0 by default."""
        get_llm()
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["temperature"] == 0.0
    
    @patch("common.llm_factory.OllamaLLM")
    def test_temperature_parameter_custom(self, mock_class):
        """get_llm(temperature=0.7) sets custom temperature."""
        get_llm(temperature=0.7)
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["temperature"] == 0.7
    
    @patch("common.llm_factory.OllamaLLM")
    def test_base_url_is_set(self, mock_class, monkeypatch):
        """get_llm() sets base_url from OLLAMA_BASE_URL."""
        with patch("common.llm_factory._BASE_URL", "http://custom:11434"):
            get_llm()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["base_url"] == "http://custom:11434"
    
    @patch("common.llm_factory.OllamaLLM")
    def test_auth_headers_included_when_api_key_set(self, mock_class):
        """get_llm() includes auth headers when API key is configured."""
        with patch("common.llm_factory._API_KEY", "test-api-key"):
            get_llm()
            call_kwargs = mock_class.call_args[1]
            assert "client_kwargs" in call_kwargs
            assert "headers" in call_kwargs["client_kwargs"]
            assert call_kwargs["client_kwargs"]["headers"]["Authorization"] == "Bearer test-api-key"
    
    @patch("common.llm_factory.OllamaLLM")
    def test_no_auth_headers_when_api_key_empty(self, mock_class):
        """get_llm() doesn't include auth header when API key is empty."""
        with patch("common.llm_factory._API_KEY", ""):
            get_llm()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["client_kwargs"]["headers"] == {}


@pytest.mark.unit
class TestGetChatLLM:
    """Unit tests for get_chat_llm()."""
    
    @patch("common.llm_factory.ChatOllama")
    def test_returns_chat_ollama_instance(self, mock_class):
        """get_chat_llm() returns a ChatOllama instance."""
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        
        chat = get_chat_llm()
        
        mock_class.assert_called_once()
        assert chat == mock_instance
    
    @patch("common.llm_factory.ChatOllama")
    def test_uses_default_model_from_env(self, mock_class):
        """get_chat_llm() uses OLLAMA_MODEL from environment."""
        with patch("common.llm_factory._DEFAULT_MODEL", "chat-model:latest"):
            get_chat_llm()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["model"] == "chat-model:latest"
    
    @patch("common.llm_factory.ChatOllama")
    def test_model_override_works(self, mock_class):
        """get_chat_llm(model='custom') overrides default model."""
        get_chat_llm(model="llama3.1:8b")
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "llama3.1:8b"
    
    @patch("common.llm_factory.ChatOllama")
    def test_json_format_mode(self, mock_class):
        """get_chat_llm(format='json') enables JSON output mode."""
        get_chat_llm(format="json")
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["format"] == "json"
    
    @patch("common.llm_factory.ChatOllama")
    def test_format_not_set_by_default(self, mock_class):
        """get_chat_llm() doesn't set format parameter by default."""
        get_chat_llm()
        call_kwargs = mock_class.call_args[1]
        assert "format" not in call_kwargs
    
    @patch("common.llm_factory.ChatOllama")
    def test_num_ctx_parameter(self, mock_class):
        """get_chat_llm(num_ctx=8192) sets context window size."""
        get_chat_llm(num_ctx=8192)
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["num_ctx"] == 8192
    
    @patch("common.llm_factory.ChatOllama")
    def test_num_ctx_not_set_by_default(self, mock_class):
        """get_chat_llm() doesn't set num_ctx by default."""
        get_chat_llm()
        call_kwargs = mock_class.call_args[1]
        assert "num_ctx" not in call_kwargs
    
    @patch("common.llm_factory.ChatOllama")
    def test_temperature_parameter(self, mock_class):
        """get_chat_llm(temperature=0.5) sets temperature."""
        get_chat_llm(temperature=0.5)
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["temperature"] == 0.5
    
    @patch("common.llm_factory.ChatOllama")
    def test_combined_parameters(self, mock_class):
        """get_chat_llm() handles multiple parameters together."""
        get_chat_llm(
            model="custom-model",
            temperature=0.8,
            format="json",
            num_ctx=4096
        )
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "custom-model"
        assert call_kwargs["temperature"] == 0.8
        assert call_kwargs["format"] == "json"
        assert call_kwargs["num_ctx"] == 4096
    
    @patch("common.llm_factory.ChatOllama")
    def test_base_url_is_set(self, mock_class):
        """get_chat_llm() sets base_url from configuration."""
        with patch("common.llm_factory._BASE_URL", "http://remote:11434"):
            get_chat_llm()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["base_url"] == "http://remote:11434"


@pytest.mark.unit
class TestGetEmbeddings:
    """Unit tests for get_embeddings()."""
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_returns_embeddings_instance(self, mock_class):
        """get_embeddings() returns an OllamaEmbeddings instance."""
        mock_instance = Mock()
        mock_class.return_value = mock_instance
        
        embeddings = get_embeddings()
        
        mock_class.assert_called_once()
        assert embeddings == mock_instance
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_uses_default_embedding_model_from_env(self, mock_class):
        """get_embeddings() uses OLLAMA_EMBEDDING_MODEL from environment."""
        with patch("common.llm_factory._DEFAULT_EMBEDDING_MODEL", "test-embed-model"):
            get_embeddings()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["model"] == "test-embed-model"
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_model_override_works(self, mock_class):
        """get_embeddings(model='custom') overrides default model."""
        get_embeddings(model="mxbai-embed-large")
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "mxbai-embed-large"
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_base_url_is_set(self, mock_class):
        """get_embeddings() sets base_url from configuration."""
        with patch("common.llm_factory._BASE_URL", "http://embed:11434"):
            get_embeddings()
            call_kwargs = mock_class.call_args[1]
            assert call_kwargs["base_url"] == "http://embed:11434"
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_auth_headers_included_when_api_key_set(self, mock_class):
        """get_embeddings() includes auth headers when API key is configured."""
        with patch("common.llm_factory._API_KEY", "embed-api-key"):
            get_embeddings()
            call_kwargs = mock_class.call_args[1]
            assert "client_kwargs" in call_kwargs
            assert call_kwargs["client_kwargs"]["headers"]["Authorization"] == "Bearer embed-api-key"


@pytest.mark.unit
class TestAuthHeaders:
    """Unit tests for _auth_headers() helper function."""
    
    @patch("common.llm_factory._API_KEY", "test-key-123")
    def test_returns_auth_header_when_api_key_set(self):
        """_auth_headers() returns Bearer token when API key is configured."""
        from common.llm_factory import _auth_headers
        headers = _auth_headers()
        assert headers == {"Authorization": "Bearer test-key-123"}
    
    @patch("common.llm_factory._API_KEY", "")
    def test_returns_empty_dict_when_api_key_empty(self):
        """_auth_headers() returns empty dict when API key is not set."""
        from common.llm_factory import _auth_headers
        headers = _auth_headers()
        assert headers == {}


@pytest.mark.integration
class TestLLMFactoryIntegration:
    """Integration tests for llm_factory module."""
    
    @patch("common.llm_factory.OllamaLLM")
    @patch("common.llm_factory.ChatOllama")
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_all_factories_can_be_called_together(
        self, mock_embeddings, mock_chat, mock_llm
    ):
        """All factory functions can be called in sequence without errors."""
        # Simulate a typical workflow
        llm = get_llm()
        chat = get_chat_llm()
        embeddings = get_embeddings()
        
        assert mock_llm.called
        assert mock_chat.called
        assert mock_embeddings.called
    
    @patch("common.llm_factory.OllamaLLM")
    @patch("common.llm_factory.ChatOllama")
    def test_different_models_for_llm_and_chat(self, mock_chat, mock_llm):
        """get_llm() and get_chat_llm() can use different models."""
        get_llm(model="model-a")
        get_chat_llm(model="model-b")
        
        llm_model = mock_llm.call_args[1]["model"]
        chat_model = mock_chat.call_args[1]["model"]
        
        assert llm_model == "model-a"
        assert chat_model == "model-b"


@pytest.mark.integration
class TestVaultIntegration:
    """Integration tests for Vault secret management in llm_factory."""
    
    @patch("common.llm_factory.OllamaLLM")
    @patch("common.vault.get_secret")
    def test_llm_factory_uses_vault_for_api_key(self, mock_get_secret, mock_llm_class):
        """LLM factory retrieves API key via Vault integration."""
        # Simulate Vault returning a key
        mock_get_secret.return_value = "vault-api-key-123"
        
        # Force module reload to trigger get_secret call
        import importlib
        import common.llm_factory
        importlib.reload(common.llm_factory)
        
        # Now create LLM
        from common.llm_factory import get_llm
        llm = get_llm()
        
        # Verify get_secret was called correctly
        mock_get_secret.assert_called_with(
            vault_key="OLLAMA_API_KEY",
            env_fallback_key="OLLAMA_API_KEY",
            default=""
        )
    
    @patch("common.llm_factory.OllamaLLM")
    def test_vault_key_used_in_auth_headers(self, mock_llm_class):
        """API key from Vault is used in authorization headers."""
        # Patch _API_KEY directly to simulate Vault retrieval
        with patch("common.llm_factory._API_KEY", "vault-retrieved-key"):
            get_llm()
            call_kwargs = mock_llm_class.call_args[1]
            headers = call_kwargs["client_kwargs"]["headers"]
            assert headers["Authorization"] == "Bearer vault-retrieved-key"
    
    @patch("common.llm_factory.ChatOllama")
    def test_vault_fallback_to_env_works(self, mock_chat_class):
        """When Vault fails, .env fallback key is used."""
        # Simulate Vault fallback returning env value
        with patch("common.llm_factory._API_KEY", "env-fallback-key"):
            get_chat_llm()
            call_kwargs = mock_chat_class.call_args[1]
            headers = call_kwargs["client_kwargs"]["headers"]
            assert headers["Authorization"] == "Bearer env-fallback-key"
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_vault_empty_key_results_in_no_auth(self, mock_embeddings_class):
        """When Vault and .env have no key, no auth headers are set."""
        with patch("common.llm_factory._API_KEY", ""):
            get_embeddings()
            call_kwargs = mock_embeddings_class.call_args[1]
            headers = call_kwargs["client_kwargs"]["headers"]
            assert headers == {}
    
    @patch("common.llm_factory.OllamaLLM")
    @patch("common.llm_factory.ChatOllama")
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_same_api_key_used_across_all_factories(
        self, mock_embeddings, mock_chat, mock_llm
    ):
        """All factory functions use the same API key from Vault/env."""
        with patch("common.llm_factory._API_KEY", "shared-api-key"):
            get_llm()
            get_chat_llm()
            get_embeddings()
            
            # All should have the same API key in headers
            llm_headers = mock_llm.call_args[1]["client_kwargs"]["headers"]
            chat_headers = mock_chat.call_args[1]["client_kwargs"]["headers"]
            embed_headers = mock_embeddings.call_args[1]["client_kwargs"]["headers"]
            
            assert llm_headers["Authorization"] == "Bearer shared-api-key"
            assert chat_headers["Authorization"] == "Bearer shared-api-key"
            assert embed_headers["Authorization"] == "Bearer shared-api-key"
