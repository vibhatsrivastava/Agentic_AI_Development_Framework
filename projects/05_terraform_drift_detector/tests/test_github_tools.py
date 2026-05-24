"""Tests for GitHub tools integration."""

import json
import pytest
from unittest.mock import Mock, patch
from src.tools.github_tools import (
    get_github_headers,
    create_github_issue,
    search_existing_issues,
    update_issue_labels,
    close_issue,
    post_issue_comment,
)


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token_12345")
    monkeypatch.setenv("GITHUB_OWNER", "test-owner")
    monkeypatch.setenv("GITHUB_REPO", "test-repo")


def test_get_github_headers():
    """Test GitHub API headers generation."""
    token = "test_token"
    headers = get_github_headers(token)
    
    assert headers["Authorization"] == "Bearer test_token"
    assert headers["Accept"] == "application/vnd.github.v3+json"
    assert headers["Content-Type"] == "application/json"


@patch("src.tools.github_tools.requests.post")
def test_create_github_issue_success(mock_post, mock_env_vars):
    """Test successful GitHub issue creation."""
    # Mock successful API response
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {
        "number": 42,
        "html_url": "https://github.com/test-owner/test-repo/issues/42",
        "title": "Test Issue",
    }
    mock_post.return_value = mock_response
    
    # Call function
    result = create_github_issue(
        owner="test-owner",
        repo="test-repo",
        title="Test Issue",
        body="Test body",
        labels=["bug", "high-priority"],
        assignees=["@user1"],
        token="test_token"
    )
    
    # Verify result
    result_data = json.loads(result)
    assert result_data["success"] is True
    assert result_data["issue_number"] == 42
    assert result_data["issue_url"] == "https://github.com/test-owner/test-repo/issues/42"
    
    # Verify API call
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://api.github.com/repos/test-owner/test-repo/issues"
    assert call_args[1]["json"]["title"] == "Test Issue"
    assert call_args[1]["json"]["labels"] == ["bug", "high-priority"]


@patch("src.tools.github_tools.requests.post")
def test_create_github_issue_failure(mock_post, mock_env_vars):
    """Test GitHub issue creation failure."""
    # Mock failed API response
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.raise_for_status.side_effect = Exception("API Error: Forbidden")
    mock_post.return_value = mock_response
    
    # Call function
    result = create_github_issue(
        owner="test-owner",
        repo="test-repo",
        title="Test Issue",
        body="Test body",
        token="invalid_token"
    )
    
    # Verify error handling
    result_data = json.loads(result)
    assert result_data["success"] is False
    assert "error" in result_data


@patch("src.tools.github_tools.requests.get")
def test_search_existing_issues_found(mock_get, mock_env_vars):
    """Test searching existing issues - found."""
    # Mock search API response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "total_count": 1,
        "items": [
            {
                "number": 99,
                "html_url": "https://github.com/test-owner/test-repo/issues/99",
                "title": "Existing Issue",
                "state": "open",
            }
        ],
    }
    mock_get.return_value = mock_response
    
    # Call function
    result = search_existing_issues(
        owner="test-owner",
        repo="test-repo",
        resource_id="i-0123456789abcdef0",
        drift_type="Tags Modified",
        token="test_token"
    )
    
    # Verify result
    result_data = json.loads(result)
    assert result_data["found"] is True
    assert result_data["issue_number"] == 99
    assert result_data["count"] == 1
    
    # Verify search query
    mock_get.assert_called_once()
    call_args = mock_get.call_args
    params = call_args[1]["params"]
    assert "i-0123456789abcdef0" in params["q"]
    assert "is:open" in params["q"]


@patch("src.tools.github_tools.requests.get")
def test_search_existing_issues_not_found(mock_get, mock_env_vars):
    """Test searching existing issues - not found."""
    # Mock empty search result
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"total_count": 0, "items": []}
    mock_get.return_value = mock_response
    
    # Call function
    result = search_existing_issues(
        owner="test-owner",
        repo="test-repo",
        resource_id="i-nonexistent",
        drift_type="Security Group Modified",
        token="test_token"
    )
    
    # Verify result
    result_data = json.loads(result)
    assert result_data["found"] is False
    assert result_data["count"] == 0


@patch("src.tools.github_tools.requests.post")
@patch("src.tools.github_tools.requests.delete")
def test_update_issue_labels(mock_delete, mock_post, mock_env_vars):
    """Test updating issue labels."""
    # Mock successful responses
    mock_post.return_value = Mock(status_code=200)
    mock_delete.return_value = Mock(status_code=200)
    
    # Call function
    result = update_issue_labels(
        owner="test-owner",
        repo="test-repo",
        issue_number=42,
        add_labels=["reviewed", "approved"],
        remove_labels=["pending"],
        token="test_token"
    )
    
    # Verify result
    result_data = json.loads(result)
    assert result_data["success"] is True
    
    # Verify API calls
    assert mock_post.call_count == 1  # Add labels
    assert mock_delete.call_count == 1  # Remove label


@patch("src.tools.github_tools.requests.patch")
@patch("src.tools.github_tools.requests.post")
def test_close_issue_with_comment(mock_post, mock_patch, mock_env_vars):
    """Test closing an issue with a comment."""
    # Mock successful responses
    mock_post.return_value = Mock(status_code=201)
    mock_patch.return_value = Mock(status_code=200)
    
    # Call function
    result = close_issue(
        owner="test-owner",
        repo="test-repo",
        issue_number=42,
        comment="Issue resolved via terraform apply",
        token="test_token"
    )
    
    # Verify result
    result_data = json.loads(result)
    assert result_data["success"] is True
    
    # Verify both API calls were made
    mock_post.assert_called_once()  # Post comment
    mock_patch.assert_called_once()  # Close issue


@patch("src.tools.github_tools.requests.post")
def test_post_issue_comment(mock_post, mock_env_vars):
    """Test posting a comment on an issue."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": 12345}
    mock_post.return_value = mock_response
    
    # Call function
    result = post_issue_comment(
        owner="test-owner",
        repo="test-repo",
        issue_number=42,
        comment="This is a test comment",
        token="test_token"
    )
    
    # Verify result
    result_data = json.loads(result)
    assert result_data["success"] is True
    assert result_data["comment_id"] == 12345
