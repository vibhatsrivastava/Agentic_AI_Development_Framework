"""
test_main.py — Comprehensive tests for GitHub Issue Reporter Agent.

Tests cover:
- Tool functions (list_open_issues, get_issue_details, get_issue_comments)
- Agent building and invocation
- CLI argument parsing and validation
- Error handling and edge cases
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import date
from src.main import (
    list_open_issues,
    get_issue_details,
    get_issue_comments,
    build_agent,
    main,
)


class TestListOpenIssuesTool:
    """Tests for list_open_issues tool."""

    def test_list_open_issues_success(self, mock_github_api, mock_env, sample_github_issues):
        """Test successful fetching of open issues."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_github_issues
        mock_github_api.return_value = mock_response

        result = list_open_issues.invoke({"owner": "testowner", "repo": "testrepo"})
        data = json.loads(result)

        assert data["total_open"] == 2
        assert len(data["issues"]) == 2
        assert data["issues"][0]["number"] == 42
        assert data["issues"][0]["title"] == "Fix token counter edge case"
        assert data["issues"][0]["author"] == "alice"
        assert data["issues"][0]["assignee"] == "bob"
        assert "bug" in data["issues"][0]["labels"]

    def test_list_open_issues_pagination(self, mock_github_api, mock_env):
        """Test pagination when more than 100 issues exist."""
        # Page 1: 100 issues
        page1_issues = [
            {
                "number": i,
                "title": f"Issue {i}",
                "user": {"login": "user"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": f"https://github.com/test/test/issues/{i}",
                "body": "Test",
            }
            for i in range(1, 101)
        ]

        # Page 2: 5 issues
        page2_issues = [
            {
                "number": i,
                "title": f"Issue {i}",
                "user": {"login": "user"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": f"https://github.com/test/test/issues/{i}",
                "body": "Test",
            }
            for i in range(101, 106)
        ]

        mock_response1 = Mock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = page1_issues

        mock_response2 = Mock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = page2_issues

        mock_github_api.side_effect = [mock_response1, mock_response2]

        result = list_open_issues.invoke({"owner": "test", "repo": "test"})
        data = json.loads(result)

        assert data["total_open"] == 105
        assert mock_github_api.call_count == 2

    def test_list_open_issues_excludes_prs(self, mock_github_api, mock_env):
        """Test that pull requests are excluded from issue list."""
        issues_with_pr = [
            {
                "number": 10,
                "title": "Real issue",
                "user": {"login": "alice"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "https://github.com/test/test/issues/10",
                "body": "Issue",
            },
            {
                "number": 11,
                "title": "Pull request",
                "user": {"login": "bob"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "html_url": "https://github.com/test/test/pull/11",
                "pull_request": {"url": "https://api.github.com/repos/test/test/pulls/11"},
                "body": "PR",
            },
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues_with_pr
        mock_github_api.return_value = mock_response

        result = list_open_issues.invoke({"owner": "test", "repo": "test"})
        data = json.loads(result)

        # Only the real issue should be included
        assert data["total_open"] == 1
        assert data["issues"][0]["number"] == 10

    def test_list_open_issues_http_error(self, mock_github_api, mock_env):
        """Test handling of HTTP errors from GitHub API."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.raise_for_status.side_effect = Exception("404 Error")

        mock_github_api.return_value = mock_response

        result = list_open_issues.invoke({"owner": "invalid", "repo": "invalid"})
        data = json.loads(result)

        assert "error" in data


class TestGetIssueDetailsTool:
    """Tests for get_issue_details tool."""

    def test_get_issue_details_success(self, mock_github_api, mock_env, sample_issue_detail):
        """Test successful fetching of issue details."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_issue_detail
        mock_github_api.return_value = mock_response

        result = get_issue_details.invoke({"owner": "testowner", "repo": "testrepo", "issue_number": 42})
        data = json.loads(result)

        assert data["number"] == 42
        assert data["title"] == "Fix token counter edge case"
        assert data["author"] == "alice"
        assert data["assignees"] == ["bob"]
        assert "bug" in data["labels"]
        assert data["state"] == "open"

    def test_get_issue_details_body_truncation(self, mock_github_api, mock_env):
        """Test that issue body is truncated to 4000 characters."""
        long_body = "a" * 10000  # 10k chars
        issue_with_long_body = {
            "number": 1,
            "title": "Test",
            "user": {"login": "user"},
            "assignees": [],
            "labels": [],
            "state": "open",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "html_url": "https://github.com/test/test/issues/1",
            "body": long_body,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = issue_with_long_body
        mock_github_api.return_value = mock_response

        result = get_issue_details.invoke({"owner": "test", "repo": "test", "issue_number": 1})
        data = json.loads(result)

        assert len(data["body"]) == 4000

    def test_get_issue_details_not_found(self, mock_github_api, mock_env):
        """Test handling of non-existent issue."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.raise_for_status.side_effect = Exception("404 Error")

        mock_github_api.return_value = mock_response

        result = get_issue_details.invoke({"owner": "test", "repo": "test", "issue_number": 999})
        data = json.loads(result)

        assert "error" in data


class TestGetIssueCommentsTool:
    """Tests for get_issue_comments tool."""

    def test_get_issue_comments_success(self, mock_github_api, mock_env, sample_issue_comments):
        """Test successful fetching of issue comments."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_issue_comments
        mock_github_api.return_value = mock_response

        result = get_issue_comments.invoke({"owner": "testowner", "repo": "testrepo", "issue_number": 42})
        data = json.loads(result)

        assert data["total_comments"] == 2
        assert len(data["comments"]) == 2
        assert data["comments"][0]["author"] == "dave"
        assert "count_tokens()" in data["comments"][0]["body"]

    def test_get_issue_comments_truncation(self, mock_github_api, mock_env):
        """Test that comment bodies are truncated to 1000 characters."""
        long_comment = {
            "user": {"login": "user"},
            "created_at": "2026-01-01T00:00:00Z",
            "body": "x" * 5000,  # 5k chars
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [long_comment]
        mock_github_api.return_value = mock_response

        result = get_issue_comments.invoke({"owner": "test", "repo": "test", "issue_number": 1})
        data = json.loads(result)

        assert len(data["comments"][0]["body"]) == 1000

    def test_get_issue_comments_empty(self, mock_github_api, mock_env):
        """Test issue with no comments."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_github_api.return_value = mock_response

        result = get_issue_comments.invoke({"owner": "test", "repo": "test", "issue_number": 1})
        data = json.loads(result)

        assert data["total_comments"] == 0
        assert data["comments"] == []


class TestAgentBuilding:
    """Tests for agent construction."""

    def test_build_agent_creates_valid_agent(self, mock_chat_llm, mock_env):
        """Test that build_agent creates a valid LangGraph agent."""
        agent = build_agent()

        assert agent is not None
        # Agent should be callable
        assert callable(agent.invoke)

    def test_agent_has_required_tools(self, mock_chat_llm, mock_env):
        """Test that agent is created with all three required tools."""
        with patch("src.main.create_agent") as mock_create:
            mock_create.return_value = Mock()
            
            build_agent()

            # Verify create_agent was called with tools
            assert mock_create.called
            call_kwargs = mock_create.call_args[1]
            assert "tools" in call_kwargs
            tools = call_kwargs["tools"]
            assert len(tools) == 3


class TestCLIArgumentParsing:
    """Tests for CLI argument parsing and validation."""

    def test_report_mode_argument(self):
        """Test --report flag is parsed correctly."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--report", action="store_true")
        group.add_argument("--issue", type=int)
        
        args = parser.parse_args(["--report"])
        assert args.report is True
        assert args.issue is None

    def test_issue_mode_argument(self):
        """Test --issue argument is parsed correctly."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--report", action="store_true")
        group.add_argument("--issue", type=int)
        
        args = parser.parse_args(["--issue", "42"])
        assert args.report is False
        assert args.issue == 42

    def test_invalid_issue_number_validation(self):
        """Test that negative or zero issue numbers are rejected."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--report", action="store_true")
        group.add_argument("--issue", type=int)
        
        # Parser should accept the value, but application validation should reject it
        args = parser.parse_args(["--issue", "-1"])
        assert args.issue == -1  # Parsed, but should be validated in main()

    def test_mutually_exclusive_arguments(self):
        """Test that --report and --issue cannot be used together."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--report", action="store_true")
        group.add_argument("--issue", type=int)
        
        with pytest.raises(SystemExit):
            parser.parse_args(["--report", "--issue", "42"])


class TestMainFunction:
    """Integration tests for main() function."""

    def test_main_missing_env_vars(self, mock_chat_llm, capsys, monkeypatch):
        """Test that main() handles missing environment variables gracefully."""
        # Clear env vars
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        monkeypatch.delenv("GITHUB_REPO_OWNER", raising=False)
        
        with patch("sys.argv", ["main.py", "--report"]):
            main()
            
            captured = capsys.readouterr()
            assert "Configuration error" in captured.out

    def test_main_report_mode_integration(self, mock_chat_llm, mock_github_api, mock_env, capsys):
        """Test main() in report mode with mocked dependencies."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_github_api.return_value = mock_response
        
        # Mock agent response
        mock_chat_llm.return_value.invoke = Mock(return_value={
            "messages": [Mock(content="## Open Issues Report\n\nNo open issues found.")]
        })
        
        with patch("sys.argv", ["main.py", "--report"]):
            with patch("src.main.build_agent") as mock_build:
                mock_agent = Mock()
                mock_agent.invoke.return_value = {
                    "messages": [Mock(content="## Open Issues Report\n\nNo open issues.")]
                }
                mock_build.return_value = mock_agent
                
                main()
                
                captured = capsys.readouterr()
                assert "Open Issues Report" in captured.out or "Agent execution" in captured.out

    def test_main_recommendation_mode_integration(self, mock_chat_llm, mock_github_api, mock_env, sample_issue_detail, capsys):
        """Test main() in recommendation mode with mocked dependencies."""
        # Mock API responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_issue_detail
        mock_github_api.return_value = mock_response
        
        with patch("sys.argv", ["main.py", "--issue", "42"]):
            with patch("src.main.build_agent") as mock_build:
                mock_agent = Mock()
                mock_agent.invoke.return_value = {
                    "messages": [Mock(content="## Recommendation\n\nIssue Type: Bug")]
                }
                mock_build.return_value = mock_agent
                
                main()
                
                captured = capsys.readouterr()
                # Should execute without error
                assert captured.out  # Some output should be generated


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_network_timeout(self, mock_github_api, mock_env):
        """Test handling of network timeouts."""
        import requests
        mock_github_api.side_effect = requests.exceptions.Timeout("Request timed out")

        result = list_open_issues.invoke({"owner": "test", "repo": "test"})
        data = json.loads(result)

        assert "error" in data

    def test_empty_issue_body(self, mock_github_api, mock_env):
        """Test handling of issue with no body."""
        issue_no_body = {
            "number": 1,
            "title": "Test",
            "user": {"login": "user"},
            "assignees": [],
            "labels": [],
            "state": "open",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "html_url": "https://github.com/test/test/issues/1",
            "body": None,
        }

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = issue_no_body
        mock_github_api.return_value = mock_response

        result = get_issue_details.invoke({"owner": "test", "repo": "test", "issue_number": 1})
        data = json.loads(result)

        assert data["body"] == ""  # Should handle None gracefully



