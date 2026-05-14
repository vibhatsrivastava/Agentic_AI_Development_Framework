"""
test_multi_repo.py — Tests for multi-repository support.

Tests cover:
- Configuration loading (load_repos_config)
- Token resolution (get_repo_token)
- Multi-repo CLI argument parsing
- Processing multiple repositories with shared and per-repo tokens
"""

import pytest
import json
import os
import sys
import tempfile
from unittest.mock import Mock, patch
from src.main import (
    load_repos_config,
    get_repo_token,
    list_open_issues,
)


def test_module_imports():
    """Test that the module imports successfully."""
    # This test ensures the module-level code is executed, including sys.path manipulation
    import src.main
    assert hasattr(src.main, 'load_repos_config')
    assert hasattr(src.main, 'get_repo_token')
    assert hasattr(src.main, 'main')


class TestReposConfigLoading:
    """Tests for load_repos_config function."""

    def test_load_valid_config(self, tmp_path):
        """Test loading a valid configuration file."""
        config_file = tmp_path / "repos.json"
        config_data = {
            "default_token": "ghp_default_token",
            "repositories": [
                {"owner": "user1", "name": "repo1"},
                {"owner": "user2", "name": "repo2", "token": "ghp_repo2_token"},
            ]
        }
        config_file.write_text(json.dumps(config_data))

        config = load_repos_config(str(config_file))

        assert config["default_token"] == "ghp_default_token"
        assert len(config["repositories"]) == 2
        assert config["repositories"][0]["owner"] == "user1"
        assert config["repositories"][1]["token"] == "ghp_repo2_token"

    def test_load_config_without_default_token(self, tmp_path):
        """Test loading a config without default_token (per-repo tokens only)."""
        config_file = tmp_path / "repos.json"
        config_data = {
            "repositories": [
                {"owner": "user1", "name": "repo1", "token": "ghp_repo1_token"},
                {"owner": "user2", "name": "repo2", "token": "ghp_repo2_token"},
            ]
        }
        config_file.write_text(json.dumps(config_data))

        config = load_repos_config(str(config_file))

        assert "default_token" not in config or config.get("default_token") is None
        assert len(config["repositories"]) == 2

    def test_load_config_file_not_found(self):
        """Test error handling when config file doesn't exist."""
        with pytest.raises(FileNotFoundError) as exc_info:
            load_repos_config("/nonexistent/path/repos.json")
        
        assert "Configuration file not found" in str(exc_info.value)

    def test_load_config_invalid_json(self, tmp_path):
        """Test error handling when config contains invalid JSON."""
        config_file = tmp_path / "repos.json"
        config_file.write_text("{ invalid json }")

        with pytest.raises(ValueError) as exc_info:
            load_repos_config(str(config_file))
        
        assert "Invalid JSON" in str(exc_info.value)

    def test_load_config_missing_repositories_key(self, tmp_path):
        """Test error handling when config missing 'repositories' key."""
        config_file = tmp_path / "repos.json"
        config_data = {"default_token": "ghp_token"}
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_repos_config(str(config_file))
        
        assert "must contain 'repositories'" in str(exc_info.value)

    def test_load_config_empty_repositories(self, tmp_path):
        """Test error handling when repositories array is empty."""
        config_file = tmp_path / "repos.json"
        config_data = {"repositories": []}
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_repos_config(str(config_file))
        
        assert "cannot be empty" in str(exc_info.value)

    def test_load_config_invalid_repository_entry(self, tmp_path):
        """Test error handling when repository entry missing required fields."""
        config_file = tmp_path / "repos.json"
        config_data = {
            "repositories": [
                {"owner": "user1"},  # Missing 'name'
            ]
        }
        config_file.write_text(json.dumps(config_data))

        with pytest.raises(ValueError) as exc_info:
            load_repos_config(str(config_file))
        
        assert "missing 'owner' or 'name'" in str(exc_info.value)


class TestGetRepoToken:
    """Tests for get_repo_token function."""

    def test_per_repo_token_takes_precedence(self):
        """Test that per-repo token overrides default token."""
        repo_config = {"owner": "user1", "name": "repo1", "token": "ghp_repo_token"}
        default_token = "ghp_default_token"

        token = get_repo_token(repo_config, default_token)

        assert token == "ghp_repo_token"

    def test_falls_back_to_default_token(self):
        """Test fallback to default token when no per-repo token."""
        repo_config = {"owner": "user1", "name": "repo1"}
        default_token = "ghp_default_token"

        token = get_repo_token(repo_config, default_token)

        assert token == "ghp_default_token"

    def test_error_when_no_token_available(self):
        """Test error when neither per-repo nor default token available."""
        repo_config = {"owner": "user1", "name": "repo1"}
        default_token = None

        with pytest.raises(ValueError) as exc_info:
            get_repo_token(repo_config, default_token)
        
        assert "No token configured" in str(exc_info.value)
        assert "user1/repo1" in str(exc_info.value)

    def test_empty_per_repo_token_falls_back(self):
        """Test that empty string token falls back to default."""
        repo_config = {"owner": "user1", "name": "repo1", "token": ""}
        default_token = "ghp_default_token"

        token = get_repo_token(repo_config, default_token)

        assert token == "ghp_default_token"


class TestToolsWithTokenParameter:
    """Tests for tools accepting optional token parameter."""

    def test_list_open_issues_with_custom_token(self, mock_github_api, sample_github_issues):
        """Test list_open_issues uses custom token when provided."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_github_issues
        mock_github_api.return_value = mock_response

        custom_token = "ghp_custom_token_123"
        result = list_open_issues.invoke({
            "owner": "testowner",
            "repo": "testrepo",
            "token": custom_token
        })

        # Verify custom token was used in the request
        call_args = mock_github_api.call_args
        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == f"Bearer {custom_token}"

        # Verify result is valid
        data = json.loads(result)
        assert data["total_open"] == 2

    def test_list_open_issues_without_token_uses_env(self, mock_github_api, mock_env, sample_github_issues):
        """Test list_open_issues falls back to GITHUB_TOKEN env var."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_github_issues
        mock_github_api.return_value = mock_response

        result = list_open_issues.invoke({
            "owner": "testowner",
            "repo": "testrepo"
            # No token parameter
        })

        # Verify env token was used
        call_args = mock_github_api.call_args
        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer test_token_123"  # From mock_env fixture

        data = json.loads(result)
        assert data["total_open"] == 2


class TestMultiRepoExample:
    """Integration test demonstrating multi-repo configuration."""

    def test_multi_repo_config_example(self, tmp_path):
        """Test a realistic multi-repo configuration scenario."""
        # Create a config with mixed token setup
        config_file = tmp_path / "repos.json"
        config_data = {
            "default_token": "ghp_shared_token",
            "repositories": [
                {"owner": "myorg", "name": "public-repo1"},  # Uses shared token
                {"owner": "myorg", "name": "public-repo2"},  # Uses shared token
                {"owner": "othercorp", "name": "private-repo", "token": "ghp_other_token"},  # Uses per-repo token
            ]
        }
        config_file.write_text(json.dumps(config_data))

        # Load and verify configuration
        config = load_repos_config(str(config_file))
        
        # Verify tokens are resolved correctly
        token1 = get_repo_token(config["repositories"][0], config.get("default_token"))
        token2 = get_repo_token(config["repositories"][1], config.get("default_token"))
        token3 = get_repo_token(config["repositories"][2], config.get("default_token"))

        assert token1 == "ghp_shared_token"  # Repo 1 uses default
        assert token2 == "ghp_shared_token"  # Repo 2 uses default
        assert token3 == "ghp_other_token"   # Repo 3 uses per-repo token


class TestHelperFunctions:
    """Tests for single-repo processing helper functions."""

    def test_process_single_repo_report(self, mock_github_api, mock_env, sample_github_issues, capsys):
        """Test process_single_repo_report helper function."""
        from src.main import process_single_repo_report
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_github_issues
        mock_github_api.return_value = mock_response

        process_single_repo_report("testowner", "testrepo", "test_token")
        
        captured = capsys.readouterr()
        assert "Open Issues Report" in captured.out
        assert "testowner/testrepo" in captured.out or "2" in captured.out  # Check for output

    def test_process_single_repo_report_error(self, mock_github_api, mock_env, capsys):
        """Test process_single_repo_report handles errors gracefully."""
        from src.main import process_single_repo_report
        
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.raise_for_status.side_effect = Exception("404 Error")
        mock_github_api.return_value = mock_response

        process_single_repo_report("invalid", "invalid", "test_token")
        
        captured = capsys.readouterr()
        assert "Report generation failed" in captured.out or "❌" in captured.out
