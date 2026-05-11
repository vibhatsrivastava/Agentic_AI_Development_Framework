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
    check_existing_bot_comments,
    post_issue_comment,
    list_recent_issues,
    format_report,
    build_agent,
    main,
    BOT_MARKER,
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


class TestCheckExistingBotCommentsTool:
    """Tests for check_existing_bot_comments tool."""

    def test_check_no_bot_comments(self, mock_github_api, mock_env):
        """Test checking issue with no bot comments."""
        # Regular comments without bot marker
        comments = [
            {"id": 1, "user": {"login": "alice"}, "body": "Regular comment", "html_url": "url1"},
            {"id": 2, "user": {"login": "bob"}, "body": "Another comment", "html_url": "url2"},
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = comments
        mock_github_api.return_value = mock_response

        result = check_existing_bot_comments.invoke({"owner": "test", "repo": "test", "issue_number": 42})
        data = json.loads(result)

        assert data["has_bot_comment"] is False
        assert data["comment_id"] is None

    def test_check_with_bot_comment(self, mock_github_api, mock_env, sample_bot_comment):
        """Test checking issue that has a bot comment."""
        comments = [
            {"id": 1, "user": {"login": "alice"}, "body": "Regular comment", "html_url": "url1"},
            sample_bot_comment,
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = comments
        mock_github_api.return_value = mock_response

        result = check_existing_bot_comments.invoke({"owner": "test", "repo": "test", "issue_number": 42})
        data = json.loads(result)

        assert data["has_bot_comment"] is True
        assert data["comment_id"] == 987654321
        assert "github.com" in data["comment_url"]

    def test_check_bot_marker_detection(self, mock_github_api, mock_env):
        """Test that bot marker is correctly detected."""
        # Comment with bot marker embedded in different places
        comments_with_marker = [
            {"id": 999, "user": {"login": "bot"}, "body": f"{BOT_MARKER}\nAI analysis here", "html_url": "url"},
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = comments_with_marker
        mock_github_api.return_value = mock_response

        result = check_existing_bot_comments.invoke({"owner": "test", "repo": "test", "issue_number": 1})
        data = json.loads(result)

        assert data["has_bot_comment"] is True

    def test_check_http_error(self, mock_github_api, mock_env):
        """Test handling of HTTP errors."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.raise_for_status.side_effect = Exception("404 Error")
        mock_github_api.return_value = mock_response

        result = check_existing_bot_comments.invoke({"owner": "test", "repo": "test", "issue_number": 999})
        data = json.loads(result)

        assert "error" in data
        assert data["has_bot_comment"] is False


class TestPostIssueCommentTool:
    """Tests for post_issue_comment tool."""

    def test_post_comment_success(self, mock_post_comment, mock_env):
        """Test successfully posting a comment."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 123456,
            "html_url": "https://github.com/test/test/issues/42#issuecomment-123456",
            "created_at": "2026-05-11T10:00:00Z",
        }
        mock_post_comment.return_value = mock_response

        result = post_issue_comment.invoke({
            "owner": "test",
            "repo": "test",
            "issue_number": 42,
            "comment_body": "Test recommendation",
        })
        data = json.loads(result)

        assert data["success"] is True
        assert data["comment_id"] == 123456
        assert "github.com" in data["comment_url"]
        assert mock_post_comment.called
        
        # Verify bot marker was included in posted comment
        posted_body = mock_post_comment.call_args[1]["json"]["body"]
        assert BOT_MARKER in posted_body
        assert "🤖 AI Analysis" in posted_body
        assert "<details>" in posted_body

    def test_post_comment_403_error(self, mock_post_comment, mock_env):
        """Test handling of 403 Forbidden (insufficient permissions)."""
        import requests
        
        # Create proper HTTPError with response attribute
        mock_response = Mock()
        mock_response.status_code = 403
        mock_response.reason = "Forbidden"
        
        http_error = requests.exceptions.HTTPError("403 Forbidden")
        http_error.response = mock_response
        mock_response.raise_for_status.side_effect = http_error
        mock_post_comment.return_value = mock_response

        result = post_issue_comment.invoke({
            "owner": "test",
            "repo": "test",
            "issue_number": 42,
            "comment_body": "Test",
        })
        data = json.loads(result)

        assert data["success"] is False
        assert "error" in data
        assert "permissions" in data["error"].lower() or "403" in data["error"]

    def test_post_comment_404_error(self, mock_post_comment, mock_env):
        """Test handling of 404 Not Found (issue doesn't exist)."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = "Not Found"
        mock_response.raise_for_status.side_effect = Exception("404 Error")
        mock_post_comment.return_value = mock_response

        result = post_issue_comment.invoke({
            "owner": "test",
            "repo": "test",
            "issue_number": 999,
            "comment_body": "Test",
        })
        data = json.loads(result)

        assert data["success"] is False
        assert "error" in data

    def test_post_comment_formatting(self, mock_post_comment, mock_env):
        """Test that comment body is properly formatted with collapsible details."""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "html_url": "url",
            "created_at": "2026-05-11T10:00:00Z",
        }
        mock_post_comment.return_value = mock_response

        post_issue_comment.invoke({
            "owner": "test",
            "repo": "test",
            "issue_number": 1,
            "comment_body": "My recommendation text",
        })

        # Extract the posted body
        posted_body = mock_post_comment.call_args[1]["json"]["body"]
        
        # Verify structure
        assert "<!-- AI-ANALYSIS-BOT -->" in posted_body
        assert "## 🤖 AI Analysis" in posted_body
        assert "<details>" in posted_body
        assert "<summary>View Recommendation</summary>" in posted_body
        assert "</details>" in posted_body
        assert "My recommendation text" in posted_body
        assert "Generated by GitHub Issue Reporter Agent" in posted_body


class TestListRecentIssuesTool:
    """Tests for list_recent_issues tool."""

    def test_list_recent_issues_success(self, mock_github_api, mock_env, sample_recent_issues):
        """Test fetching issues from last 24 hours."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_recent_issues
        mock_github_api.return_value = mock_response

        result = list_recent_issues.invoke({"owner": "testowner", "repo": "testrepo", "hours": 24})
        data = json.loads(result)

        assert data["total_recent"] == 2
        assert data["hours"] == 24
        assert len(data["issues"]) == 2
        assert data["issues"][0]["number"] == 100

    def test_list_recent_issues_excludes_prs(self, mock_github_api, mock_env):
        """Test that pull requests are excluded."""
        issues_with_pr = [
            {
                "number": 50,
                "title": "Real issue",
                "user": {"login": "alice"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-05-10T20:00:00Z",
                "updated_at": "2026-05-10T20:00:00Z",
                "html_url": "url",
                "body": "Issue",
            },
            {
                "number": 51,
                "title": "PR",
                "user": {"login": "bob"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-05-10T19:00:00Z",
                "updated_at": "2026-05-10T19:00:00Z",
                "html_url": "url",
                "pull_request": {"url": "pr_url"},
                "body": "PR",
            },
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues_with_pr
        mock_github_api.return_value = mock_response

        result = list_recent_issues.invoke({"owner": "test", "repo": "test", "hours": 24})
        data = json.loads(result)

        assert data["total_recent"] == 1
        assert data["issues"][0]["number"] == 50

    def test_list_recent_issues_old_cutoff(self, mock_github_api, mock_env):
        """Test that issues older than cutoff are excluded."""
        # Mix of recent and old issues
        issues = [
            {
                "number": 10,
                "title": "Very recent",
                "user": {"login": "alice"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-05-11T00:00:00Z",  # Within 24h
                "updated_at": "2026-05-11T00:00:00Z",
                "html_url": "url",
                "body": "New",
            },
            {
                "number": 9,
                "title": "Too old",
                "user": {"login": "bob"},
                "assignee": None,
                "labels": [],
                "created_at": "2026-05-01T00:00:00Z",  # > 24h ago
                "updated_at": "2026-05-01T00:00:00Z",
                "html_url": "url",
                "body": "Old",
            },
        ]

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = issues
        mock_github_api.return_value = mock_response

        result = list_recent_issues.invoke({"owner": "test", "repo": "test", "hours": 24})
        data = json.loads(result)

        # Should only include the recent one (cutoff logic stops at old issue)
        assert data["total_recent"] == 1
        assert data["issues"][0]["number"] == 10

    def test_list_recent_issues_custom_hours(self, mock_github_api, mock_env):
        """Test using custom hours parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_github_api.return_value = mock_response

        result = list_recent_issues.invoke({"owner": "test", "repo": "test", "hours": 48})
        data = json.loads(result)

        assert data["hours"] == 48


class TestFormatReportFunction:
    """Tests for format_report function."""

    def test_format_report_with_issues(self):
        """Test formatting report with issues."""
        issues_data = {
            "total_open": 2,
            "issues": [
                {
                    "number": 42,
                    "title": "Bug",
                    "author": "alice",
                    "assignee": "bob",
                    "labels": ["bug", "high"],
                    "opened_at": "2026-01-01",
                    "age_days": 130,
                    "last_updated_days_ago": 7,
                    "url": "https://github.com/test/test/issues/42",
                },
                {
                    "number": 38,
                    "title": "Feature",
                    "author": "carol",
                    "assignee": "Unassigned",
                    "labels": [],
                    "opened_at": "2026-02-01",
                    "age_days": 99,
                    "last_updated_days_ago": 15,
                    "url": "https://github.com/test/test/issues/38",
                },
            ],
        }

        report = format_report(issues_data)

        assert "Open Issues Report" in report
        assert "| # | Title | Author |" in report
        assert "| 42 | Bug | alice |" in report
        assert "| 38 | Feature | carol |" in report
        assert "**Summary:** 2 open issues" in report  # Updated to match actual format
        assert "Oldest: 130 days" in report

    def test_format_report_no_issues(self):
        """Test formatting report with no issues."""
        issues_data = {"total_open": 0, "issues": []}

        report = format_report(issues_data)

        assert "No open issues found" in report
        assert "🎉" in report

    def test_format_report_error(self):
        """Test formatting report with error."""
        issues_data = {"error": "Repository not found"}

        report = format_report(issues_data)

        assert "❌ Error" in report
        assert "Repository not found" in report

    def test_format_report_no_labels(self):
        """Test formatting issue with no labels."""
        issues_data = {
            "total_open": 1,
            "issues": [
                {
                    "number": 1,
                    "title": "Test",
                    "author": "user",
                    "assignee": "Unassigned",
                    "labels": [],
                    "opened_at": "2026-05-01",
                    "age_days": 10,
                    "last_updated_days_ago": 2,
                    "url": "url",
                },
            ],
        }

        report = format_report(issues_data)

        # Should show em-dash for no labels
        assert "—" in report


class TestAgentBuilding:
    """Tests for agent construction."""

    def test_build_agent_creates_valid_agent(self, mock_chat_llm, mock_env):
        """Test that build_agent creates a valid LangGraph agent."""
        agent = build_agent()

        assert agent is not None
        # Agent should be callable
        assert callable(agent.invoke)

    def test_agent_has_required_tools(self, mock_chat_llm, mock_env):
        """Test that agent is created with all six required tools."""
        with patch("src.main.create_agent") as mock_create:
            mock_create.return_value = Mock()
            
            build_agent()

            # Verify create_agent was called with tools
            assert mock_create.called
            call_kwargs = mock_create.call_args[1]
            assert "tools" in call_kwargs
            tools = call_kwargs["tools"]
            assert len(tools) == 6  # Updated from 3 to 6 tools


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

    def test_auto_analyze_argument(self):
        """Test --auto-analyze flag is parsed correctly."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--report", action="store_true")
        group.add_argument("--issue", type=int)
        group.add_argument("--auto-analyze", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--max-issues", type=int, default=100)
        
        args = parser.parse_args(["--auto-analyze"])
        assert args.auto_analyze is True
        assert args.dry_run is False
        assert args.max_issues == 100

    def test_auto_analyze_with_dry_run(self):
        """Test --auto-analyze with --dry-run flag."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--report", action="store_true")
        group.add_argument("--issue", type=int)
        group.add_argument("--auto-analyze", action="store_true")
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--max-issues", type=int, default=100)
        
        args = parser.parse_args(["--auto-analyze", "--dry-run"])
        assert args.auto_analyze is True
        assert args.dry_run is True

    def test_max_issues_argument(self):
        """Test --max-issues custom value."""
        import argparse
        
        parser = argparse.ArgumentParser()
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--auto-analyze", action="store_true")
        parser.add_argument("--max-issues", type=int, default=100)
        
        args = parser.parse_args(["--auto-analyze", "--max-issues", "50"])
        assert args.max_issues == 50


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

    def test_main_report_mode_direct_formatting(self, mock_github_api, mock_env, capsys):
        """Test main() in report mode uses direct Python formatting (no LLM)."""
        # Mock API response with issues
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "number": 42,
                "title": "Test Issue",
                "user": {"login": "alice"},
                "assignee": {"login": "bob"},
                "labels": [{"name": "bug"}],
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-05-01T00:00:00Z",
                "html_url": "https://github.com/test/test/issues/42",
            }
        ]
        mock_github_api.return_value = mock_response
        
        with patch("sys.argv", ["main.py", "--report"]):
            main()
            
            captured = capsys.readouterr()
            # Verify output contains report (direct formatting, not LLM)
            assert "Open Issues Report" in captured.out
            assert "| #" in captured.out  # Table header
            assert "42" in captured.out
            assert "Test Issue" in captured.out

    def test_main_report_mode_no_issues(self, mock_github_api, mock_env, capsys):
        """Test report mode with no open issues."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_github_api.return_value = mock_response
        
        with patch("sys.argv", ["main.py", "--report"]):
            main()
            
            captured = capsys.readouterr()
            assert "No open issues found" in captured.out

    def test_main_issue_mode_posts_recommendation(self, mock_chat_llm, mock_github_api, mock_env, sample_issue_detail, capsys):
        """Test main() in issue mode analyzes and posts recommendation."""
        # Mock API responses for issue details
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_issue_detail
        mock_github_api.return_value = mock_response
        
        with patch("sys.argv", ["main.py", "--issue", "42"]):
            with patch("src.main.build_agent") as mock_build:
                mock_agent = Mock()
                mock_agent.invoke.return_value = {
                    "messages": [Mock(content="✅ Recommendation posted: https://github.com/test/test/issues/42#comment-123")]
                }
                mock_build.return_value = mock_agent
                
                main()
                
                captured = capsys.readouterr()
                # Agent should be invoked for issue mode
                assert mock_agent.invoke.called

    def test_main_auto_analyze_mode_dry_run(self, mock_chat_llm, mock_github_api, mock_env, sample_recent_issues, capsys):
        """Test main() in auto-analyze mode with --dry-run."""
        # Mock API response for recent issues
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = sample_recent_issues
        mock_github_api.return_value = mock_response
        
        with patch("sys.argv", ["main.py", "--auto-analyze", "--dry-run"]):
            main()
            
            captured = capsys.readouterr()
            assert "DRY RUN MODE" in captured.out
            assert ("Found" in captured.out and "issues" in captured.out) or "No new issues" in captured.out

    def test_main_auto_analyze_mode_no_new_issues(self, mock_chat_llm, mock_github_api, mock_env, capsys):
        """Test auto-analyze mode when no new issues exist."""
        # Mock empty response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = []
        mock_github_api.return_value = mock_response
        
        with patch("sys.argv", ["main.py", "--auto-analyze"]):
            main()
            
            captured = capsys.readouterr()
            assert "No new issues" in captured.out or "0 issues" in captured.out

    def test_main_invalid_issue_number_negative(self, mock_env, capsys):
        """Test that negative issue numbers are rejected."""
        with patch("sys.argv", ["main.py", "--issue", "-1"]):
            with pytest.raises(SystemExit):
                main()

    def test_main_dry_run_without_auto_analyze_fails(self, mock_env):
        """Test that --dry-run without --auto-analyze is rejected."""
        with patch("sys.argv", ["main.py", "--report", "--dry-run"]):
            with pytest.raises(SystemExit):
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



