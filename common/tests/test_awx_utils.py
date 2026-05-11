"""
test_awx_utils.py — Unit tests for AWX utility functions.

Tests helper functions for AWX integration including parameter extraction,
output formatting, and project validation.
"""

import json
import os
import pytest
from pathlib import Path

from common.awx_utils import (
    extract_agent_params,
    format_awx_output,
    validate_project_structure,
    load_env_from_dict,
)


class TestExtractAgentParams:
    """Test parameter extraction from environment variables."""
    
    def test_extract_empty_params(self, monkeypatch):
        """Test extraction when no params are set."""
        # Clear any existing env vars
        for key in ["CITY", "GITHUB_REPO", "LOG_LEVEL"]:
            monkeypatch.delenv(key, raising=False)
        
        params = extract_agent_params()
        assert isinstance(params, dict)
        assert len(params) == 0
    
    def test_extract_weather_params(self, monkeypatch):
        """Test extraction of weather agent parameters."""
        monkeypatch.setenv("CITY", "London")
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        
        params = extract_agent_params()
        assert params["city"] == "London"
        assert params["log_level"] == "INFO"
    
    def test_extract_github_params(self, monkeypatch):
        """Test extraction of GitHub agent parameters."""
        monkeypatch.setenv("GITHUB_REPO", "owner/repo")
        monkeypatch.setenv("GITHUB_ISSUE_NUMBER", "42")
        
        params = extract_agent_params()
        assert params["github_repo"] == "owner/repo"
        assert params["github_issue_number"] == "42"
    
    def test_extract_mixed_params(self, monkeypatch):
        """Test extraction of multiple parameter types."""
        monkeypatch.setenv("CITY", "Paris")
        monkeypatch.setenv("GITHUB_REPO", "test/repo")
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        monkeypatch.setenv("CUSTOM_PARAM_1", "custom_value")
        
        params = extract_agent_params()
        assert params["city"] == "Paris"
        assert params["github_repo"] == "test/repo"
        assert params["log_level"] == "DEBUG"
        assert params["custom_param_1"] == "custom_value"
    
    def test_extract_ignores_empty_values(self, monkeypatch):
        """Test that empty string values are ignored."""
        monkeypatch.setenv("CITY", "")
        monkeypatch.setenv("LOG_LEVEL", "INFO")
        
        params = extract_agent_params()
        assert "city" not in params
        assert params["log_level"] == "INFO"


class TestFormatAwxOutput:
    """Test AWX output formatting."""
    
    def test_format_success_output(self):
        """Test formatting successful agent output."""
        result = {
            "status": "success",
            "result": "Agent completed",
            "metadata": {"agent": "test_agent", "execution_time": 1.5}
        }
        
        output = format_awx_output(result)
        assert isinstance(output, str)
        
        parsed = json.loads(output)
        assert parsed["status"] == "success"
        assert parsed["result"] == "Agent completed"
        assert parsed["metadata"]["agent"] == "test_agent"
    
    def test_format_error_output(self):
        """Test formatting error output."""
        result = {
            "status": "error",
            "error": "Agent failed",
            "metadata": {"agent": "test_agent"}
        }
        
        output = format_awx_output(result)
        parsed = json.loads(output)
        
        assert parsed["status"] == "error"
        assert parsed["error"] == "Agent failed"
    
    def test_format_output_with_unicode(self):
        """Test formatting output with unicode characters."""
        result = {
            "status": "success",
            "result": "Temperature: 15°C in München",
            "metadata": {"agent": "test_agent"}
        }
        
        output = format_awx_output(result)
        parsed = json.loads(output)
        
        assert "15°C" in parsed["result"]
        assert "München" in parsed["result"]
    
    def test_format_output_with_non_serializable(self):
        """Test formatting output with non-JSON-serializable objects."""
        class CustomObject:
            pass
        
        result = {
            "status": "success",
            "result": CustomObject(),
            "metadata": {}
        }
        
        output = format_awx_output(result)
        parsed = json.loads(output)
        
        # Should fallback to error output
        assert parsed["status"] == "error"
        assert "Failed to serialize" in parsed["error"]


class TestValidateProjectStructure:
    """Test project structure validation."""
    
    def test_validate_nonexistent_project(self, tmp_path):
        """Test validation of nonexistent project."""
        repo_root = tmp_path
        (repo_root / "projects").mkdir()
        
        with pytest.raises(FileNotFoundError, match="Project directory not found"):
            validate_project_structure("nonexistent_agent", repo_root)
    
    def test_validate_project_without_src(self, tmp_path):
        """Test validation of project without src directory."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        project_path.mkdir(parents=True)
        
        with pytest.raises(FileNotFoundError, match="Source directory not found"):
            validate_project_structure("test_agent", repo_root)
    
    def test_validate_project_without_main_py(self, tmp_path):
        """Test validation of project without main.py."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        src_path.mkdir(parents=True)
        
        with pytest.raises(FileNotFoundError, match="Main module not found"):
            validate_project_structure("test_agent", repo_root)
    
    def test_validate_project_without_venv(self, tmp_path):
        """Test validation of project without virtual environment."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        src_path.mkdir(parents=True)
        (src_path / "main.py").touch()
        
        with pytest.raises(FileNotFoundError, match="Virtual environment not found"):
            validate_project_structure("test_agent", repo_root)
    
    def test_validate_complete_project(self, tmp_path):
        """Test validation of complete project structure."""
        repo_root = tmp_path
        project_path = repo_root / "projects" / "test_agent"
        src_path = project_path / "src"
        venv_path = project_path / ".venv"
        
        src_path.mkdir(parents=True)
        venv_path.mkdir(parents=True)
        (src_path / "main.py").touch()
        
        # Should not raise any exception
        validate_project_structure("test_agent", repo_root)


class TestLoadEnvFromDict:
    """Test loading environment variables from dictionary."""
    
    def test_load_empty_dict(self):
        """Test loading empty dictionary."""
        load_env_from_dict({})
        # Should not raise any exception
    
    def test_load_single_variable(self):
        """Test loading single environment variable."""
        load_env_from_dict({"TEST_VAR": "test_value"})
        assert os.getenv("TEST_VAR") == "test_value"
    
    def test_load_multiple_variables(self):
        """Test loading multiple environment variables."""
        env_dict = {
            "VAR1": "value1",
            "VAR2": "value2",
            "VAR3": "value3",
        }
        load_env_from_dict(env_dict)
        
        assert os.getenv("VAR1") == "value1"
        assert os.getenv("VAR2") == "value2"
        assert os.getenv("VAR3") == "value3"
    
    def test_load_overwrites_existing(self):
        """Test that loading overwrites existing environment variables."""
        os.environ["EXISTING_VAR"] = "old_value"
        load_env_from_dict({"EXISTING_VAR": "new_value"})
        
        assert os.getenv("EXISTING_VAR") == "new_value"
    
    def test_load_ignores_none_values(self):
        """Test that None values are ignored."""
        os.environ["TEST_VAR"] = "original"
        load_env_from_dict({"TEST_VAR": None})
        
        # Should remain unchanged
        assert os.getenv("TEST_VAR") == "original"
    
    def test_load_converts_to_string(self):
        """Test that non-string values are converted to strings."""
        load_env_from_dict({
            "INT_VAR": 123,
            "FLOAT_VAR": 45.67,
            "BOOL_VAR": True,
        })
        
        assert os.getenv("INT_VAR") == "123"
        assert os.getenv("FLOAT_VAR") == "45.67"
        assert os.getenv("BOOL_VAR") == "True"
