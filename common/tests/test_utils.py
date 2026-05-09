"""
test_utils.py — Comprehensive tests for common/utils.py

Tests cover:
- get_logger() returns correct logger with proper configuration
- Logger respects LOG_LEVEL environment variable
- require_env() returns values when set
- require_env() raises errors when missing or empty

Coverage target: >= 90%
"""

import sys
import os

# Add repo root to Python path to enable imports from common/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import pytest
import logging
from common.utils import get_logger, require_env


@pytest.fixture
def reset_logging():
    """Reset logging configuration before each test to allow basicConfig() to work."""
    # Clear all handlers from root logger
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    # Reset root logger level
    root.setLevel(logging.WARNING)
    yield
    # Clean up after test
    for handler in root.handlers[:]:
        root.removeHandler(handler)


@pytest.mark.unit
class TestGetLogger:
    """Unit tests for get_logger()."""
    
    def test_returns_logger_instance(self):
        """get_logger() returns a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_respects_log_level_from_env_debug(self, monkeypatch, reset_logging):
        """Logger uses DEBUG level when LOG_LEVEL=DEBUG."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        logger = get_logger("test_debug")
        # Check the logger's effective level (considers root + handlers)
        assert logger.getEffectiveLevel() == logging.DEBUG
    
    def test_respects_log_level_from_env_warning(self, monkeypatch, reset_logging):
        """Logger uses WARNING level when LOG_LEVEL=WARNING."""
        monkeypatch.setenv("LOG_LEVEL", "WARNING")
        logger = get_logger("test_warning")
        assert logger.getEffectiveLevel() == logging.WARNING
    
    def test_respects_log_level_from_env_error(self, monkeypatch, reset_logging):
        """Logger uses ERROR level when LOG_LEVEL=ERROR."""
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        logger = get_logger("test_error")
        assert logger.getEffectiveLevel() == logging.ERROR
    
    def test_defaults_to_info_when_log_level_unset(self, monkeypatch, reset_logging):
        """Logger defaults to INFO when LOG_LEVEL is not set."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        logger = get_logger("test_default")
        # Should default to INFO
        assert logger.getEffectiveLevel() == logging.INFO
    
    def test_handles_invalid_log_level_gracefully(self, monkeypatch, reset_logging):
        """Logger defaults to INFO when LOG_LEVEL is invalid."""
        monkeypatch.setenv("LOG_LEVEL", "INVALID_LEVEL")
        logger = get_logger("test_invalid")
        # Should fall back to INFO (default in getattr)
        assert logger.getEffectiveLevel() == logging.INFO
    
    def test_logger_name_is_preserved(self):
        """get_logger() preserves the name passed to it."""
        names = ["module1", "module2", "test.submodule"]
        for name in names:
            logger = get_logger(name)
            assert logger.name == name


@pytest.mark.unit
class TestRequireEnv:
    """Unit tests for require_env()."""
    
    def test_returns_value_when_set(self, monkeypatch):
        """require_env() returns the env var value when set."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = require_env("TEST_VAR")
        assert result == "test_value"
    
    def test_returns_value_with_special_characters(self, monkeypatch):
        """require_env() correctly returns values with special chars."""
        special_value = "http://localhost:11434?param=value&key=123"
        monkeypatch.setenv("SPECIAL_VAR", special_value)
        result = require_env("SPECIAL_VAR")
        assert result == special_value
    
    def test_raises_error_when_missing(self, monkeypatch):
        """require_env() raises EnvironmentError when var is missing."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        with pytest.raises(EnvironmentError, match="MISSING_VAR"):
            require_env("MISSING_VAR")
    
    def test_raises_error_when_empty(self, monkeypatch):
        """require_env() raises EnvironmentError when var is empty string."""
        monkeypatch.setenv("EMPTY_VAR", "")
        with pytest.raises(EnvironmentError, match="EMPTY_VAR"):
            require_env("EMPTY_VAR")
    
    def test_error_message_mentions_env_example(self, monkeypatch):
        """Error message guides user to .env.example."""
        monkeypatch.delenv("MISSING_VAR", raising=False)
        with pytest.raises(EnvironmentError, match=".env.example"):
            require_env("MISSING_VAR")
    
    def test_error_message_includes_variable_name(self, monkeypatch):
        """Error message includes the name of the missing variable."""
        monkeypatch.delenv("MY_CUSTOM_VAR", raising=False)
        with pytest.raises(EnvironmentError, match="MY_CUSTOM_VAR"):
            require_env("MY_CUSTOM_VAR")
    
    def test_works_with_existing_env_vars(self):
        """require_env() works with environment variables already set in system."""
        # Use a variable that's likely to be set (or set it temporarily)
        os.environ["TEST_EXISTING"] = "existing_value"
        try:
            result = require_env("TEST_EXISTING")
            assert result == "existing_value"
        finally:
            del os.environ["TEST_EXISTING"]


@pytest.mark.integration
class TestUtilsIntegration:
    """Integration tests for utils module components working together."""
    
    def test_logger_can_log_at_various_levels(self, monkeypatch):
        """Logger successfully logs messages at different levels."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        logger = get_logger("integration_test")
        
        # These should not raise exceptions
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")
    
    def test_require_env_and_logger_work_together(self, monkeypatch):
        """require_env() can be used with logger for config validation."""
        monkeypatch.setenv("CONFIG_VALUE", "test_config")
        logger = get_logger("config_test")
        
        # Typical usage pattern
        config_value = require_env("CONFIG_VALUE")
        logger.info(f"Loaded config: {config_value}")
        
        assert config_value == "test_config"
