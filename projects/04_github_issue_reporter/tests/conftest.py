"""
conftest.py — pytest fixtures for 04_github_issue_reporter.
"""

import sys
import os
import pytest
from unittest.mock import Mock, MagicMock
from datetime import date

# Add project root to sys.path to enable "from src.main import ..." imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# Remove any cached src.main from other projects to ensure we get THIS project's src.main
if 'src.main' in sys.modules:
    del sys.modules['src.main']
if 'src' in sys.modules:
    del sys.modules['src']

@pytest.fixture
def mock_chat_llm(mocker):
    """Mock ChatOllama for testing agents (no real API calls)."""
    mock = Mock()
    mock.invoke.return_value = {
        "messages": [
            Mock(content="Mocked agent response with structured recommendation")
        ]
    }
    mocker.patch("common.llm_factory.get_chat_llm", return_value=mock)
    return mock


@pytest.fixture
def mock_github_api(mocker):
    """Mock requests.get for GitHub API calls (no real HTTP calls)."""
    return mocker.patch("src.main.requests.get")


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    monkeypatch.setenv("GITHUB_TOKEN", "test_token_123")
    monkeypatch.setenv("GITHUB_REPO_OWNER", "testowner")
    monkeypatch.setenv("GITHUB_REPO_NAME", "testrepo")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://localhost:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.2:3b")


@pytest.fixture
def sample_github_issues():
    """Sample GitHub API response for open issues."""
    return [
        {
            "number": 42,
            "title": "Fix token counter edge case",
            "user": {"login": "alice"},
            "assignee": {"login": "bob"},
            "labels": [{"name": "bug"}, {"name": "priority:high"}],
            "created_at": "2026-04-01T10:00:00Z",
            "updated_at": "2026-05-04T15:30:00Z",
            "html_url": "https://github.com/testowner/testrepo/issues/42",
            "body": "Token counter fails with empty input",
        },
        {
            "number": 38,
            "title": "Add Redis caching integration",
            "user": {"login": "carol"},
            "assignee": None,
            "labels": [{"name": "enhancement"}],
            "created_at": "2026-03-15T08:00:00Z",
            "updated_at": "2026-04-26T12:00:00Z",
            "html_url": "https://github.com/testowner/testrepo/issues/38",
            "body": "We need Redis caching support",
        },
    ]


@pytest.fixture
def sample_issue_detail():
    """Sample GitHub API response for single issue details."""
    return {
        "number": 42,
        "title": "Fix token counter edge case",
        "user": {"login": "alice"},
        "assignees": [{"login": "bob"}],
        "labels": [{"name": "bug"}, {"name": "priority:high"}],
        "state": "open",
        "created_at": "2026-04-01T10:00:00Z",
        "updated_at": "2026-05-04T15:30:00Z",
        "html_url": "https://github.com/testowner/testrepo/issues/42",
        "body": "Token counter fails when given an empty string input. " * 100,  # Long body
    }


@pytest.fixture
def sample_issue_comments():
    """Sample GitHub API response for issue comments."""
    return [
        {
            "user": {"login": "dave"},
            "created_at": "2026-04-02T09:00:00Z",
            "body": "I can reproduce this bug. It happens in count_tokens().",
        },
        {
            "user": {"login": "eve"},
            "created_at": "2026-04-03T14:00:00Z",
            "body": "We should add input validation before split().",
        },
    ]


@pytest.fixture
def sample_bot_comment():
    """Sample bot comment with marker."""
    return {
        "id": 987654321,
        "user": {"login": "github-bot"},
        "created_at": "2026-05-01T12:00:00Z",
        "html_url": "https://github.com/testowner/testrepo/issues/42#issuecomment-987654321",
        "body": "<!-- AI-ANALYSIS-BOT -->\n## 🤖 AI Analysis\n\n<details>\n<summary>View Recommendation</summary>\n\nIssue Type: Bug\n\n</details>",
    }


@pytest.fixture
def sample_recent_issues():
    """Sample GitHub API response for recent issues (last 24 hours)."""
    from datetime import datetime, timedelta, timezone
    
    # Generate timestamps that are always within the last 24 hours
    now = datetime.now(timezone.utc)
    six_hours_ago = now - timedelta(hours=6)
    twelve_hours_ago = now - timedelta(hours=12)
    
    return [
        {
            "number": 100,
            "title": "New feature request",
            "user": {"login": "alice"},
            "assignee": None,
            "labels": [{"name": "feature"}],
            "created_at": six_hours_ago.isoformat().replace("+00:00", "Z"),
            "updated_at": six_hours_ago.isoformat().replace("+00:00", "Z"),
            "html_url": "https://github.com/testowner/testrepo/issues/100",
            "body": "Add support for new feature",
        },
        {
            "number": 99,
            "title": "Bug report",
            "user": {"login": "bob"},
            "assignee": {"login": "alice"},
            "labels": [{"name": "bug"}],
            "created_at": twelve_hours_ago.isoformat().replace("+00:00", "Z"),
            "updated_at": twelve_hours_ago.isoformat().replace("+00:00", "Z"),
            "html_url": "https://github.com/testowner/testrepo/issues/99",
            "body": "Something is broken",
        },
    ]


@pytest.fixture
def mock_post_comment(mocker):
    """Mock requests.post for posting comments to GitHub."""
    return mocker.patch("src.main.requests.post")


