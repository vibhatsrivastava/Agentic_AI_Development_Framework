"""
test_teams_notification.py — Tests for Microsoft Teams notification feature.

Tests the send_teams_notification function to ensure:
- Adaptive card payload is correctly formatted
- Webhook URL is optional (feature is disabled if not configured)
- HTTP errors are handled gracefully
- Notification doesn't break the agent if it fails
"""

import pytest
import json
from unittest.mock import Mock, patch
import os
import sys

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import the function to test
from src.main import send_teams_notification


def test_teams_notification_disabled_when_webhook_not_configured(monkeypatch):
    """Test that Teams notification is skipped if MS_TEAMS_WEBHOOK_URL is not set."""
    # Ensure webhook URL is not set
    monkeypatch.delenv("MS_TEAMS_WEBHOOK_URL", raising=False)
    
    # Call function
    result = send_teams_notification(
        owner="testowner",
        repo="testrepo",
        issue_number=123,
        issue_title="Test Issue",
        issue_url="https://github.com/testowner/testrepo/issues/123",
        comment_url="https://github.com/testowner/testrepo/issues/123#issuecomment-456"
    )
    
    # Should return False (notification skipped)
    assert result is False


@patch('src.main.requests.post')
def test_teams_notification_success(mock_post, monkeypatch):
    """Test successful Teams notification with valid webhook URL."""
    # Set webhook URL
    monkeypatch.setenv("MS_TEAMS_WEBHOOK_URL", "https://test.webhook.office.com/test")
    
    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    # Call function
    result = send_teams_notification(
        owner="testowner",
        repo="testrepo",
        issue_number=123,
        issue_title="Test Issue",
        issue_url="https://github.com/testowner/testrepo/issues/123",
        comment_url="https://github.com/testowner/testrepo/issues/123#issuecomment-456"
    )
    
    # Should return True (notification sent)
    assert result is True
    
    # Verify HTTP request was made
    assert mock_post.called
    assert mock_post.call_count == 1
    
    # Verify webhook URL was used
    call_args = mock_post.call_args
    assert call_args[0][0] == "https://test.webhook.office.com/test"
    
    # Verify payload structure
    payload = call_args[1]["json"]
    assert payload["type"] == "message"
    assert len(payload["attachments"]) == 1
    assert payload["attachments"][0]["contentType"] == "application/vnd.microsoft.card.adaptive"
    
    # Verify adaptive card structure
    card = payload["attachments"][0]["content"]
    assert card["type"] == "AdaptiveCard"
    assert card["version"] == "1.4"
    assert len(card["body"]) == 3  # Header, body, facts
    assert len(card["actions"]) == 2  # Two buttons


@patch('src.main.requests.post')
def test_teams_notification_adaptive_card_content(mock_post, monkeypatch):
    """Test that adaptive card contains correct content."""
    # Set webhook URL
    monkeypatch.setenv("MS_TEAMS_WEBHOOK_URL", "https://test.webhook.office.com/test")
    
    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    # Call function
    send_teams_notification(
        owner="vibhatsrivastava",
        repo="TestRepo",
        issue_number=42,
        issue_title="Add Teams Integration",
        issue_url="https://github.com/vibhatsrivastava/TestRepo/issues/42",
        comment_url="https://github.com/vibhatsrivastava/TestRepo/issues/42#issuecomment-789"
    )
    
    # Get payload
    payload = mock_post.call_args[1]["json"]
    card = payload["attachments"][0]["content"]
    
    # Verify header
    header = card["body"][0]
    assert header["style"] == "Good"  # Green color for success
    
    # Verify body contains issue number and title
    body = card["body"][1]
    issue_text = body["items"][0]["text"]
    assert "Issue #42" in issue_text
    assert "Add Teams Integration" in issue_text
    assert "vibhatsrivastava/TestRepo/issues/42" in issue_text
    
    # Verify facts
    facts = card["body"][2]["facts"]
    assert len(facts) == 3
    assert facts[0]["title"] == "Repository:"
    assert facts[0]["value"] == "vibhatsrivastava/TestRepo"
    assert facts[1]["title"] == "Issue Number:"
    assert facts[1]["value"] == "#42"
    assert facts[2]["title"] == "Status:"
    assert facts[2]["value"] == "Analysis Posted"
    
    # Verify actions
    actions = card["actions"]
    assert len(actions) == 2
    assert actions[0]["type"] == "Action.OpenUrl"
    assert actions[0]["title"] == "View Issue on GitHub"
    assert actions[0]["url"] == "https://github.com/vibhatsrivastava/TestRepo/issues/42"
    assert actions[1]["title"] == "View AI Recommendation"
    assert actions[1]["url"] == "https://github.com/vibhatsrivastava/TestRepo/issues/42#issuecomment-789"


@patch('src.main.requests.post')
def test_teams_notification_handles_http_error(mock_post, monkeypatch):
    """Test that HTTP errors are handled gracefully."""
    # Set webhook URL
    monkeypatch.setenv("MS_TEAMS_WEBHOOK_URL", "https://test.webhook.office.com/test")
    
    # Mock HTTP error
    mock_post.side_effect = Exception("Network error")
    
    # Call function
    result = send_teams_notification(
        owner="testowner",
        repo="testrepo",
        issue_number=123,
        issue_title="Test Issue",
        issue_url="https://github.com/testowner/testrepo/issues/123",
        comment_url="https://github.com/testowner/testrepo/issues/123#issuecomment-456"
    )
    
    # Should return False (notification failed but didn't raise exception)
    assert result is False


@patch('src.main.requests.post')
def test_teams_notification_json_valid(mock_post, monkeypatch):
    """Test that the payload is valid JSON."""
    # Set webhook URL
    monkeypatch.setenv("MS_TEAMS_WEBHOOK_URL", "https://test.webhook.office.com/test")
    
    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.raise_for_status = Mock()
    mock_post.return_value = mock_response
    
    # Call function
    send_teams_notification(
        owner="testowner",
        repo="testrepo",
        issue_number=123,
        issue_title="Test Issue",
        issue_url="https://github.com/testowner/testrepo/issues/123",
        comment_url="https://github.com/testowner/testrepo/issues/123#issuecomment-456"
    )
    
    # Get payload and verify it's valid JSON
    payload = mock_post.call_args[1]["json"]
    json_str = json.dumps(payload)
    parsed = json.loads(json_str)  # Should not raise JSONDecodeError
    assert parsed is not None


def test_teams_notification_with_special_characters(monkeypatch):
    """Test that special characters in issue title are handled correctly."""
    # Set webhook URL
    monkeypatch.setenv("MS_TEAMS_WEBHOOK_URL", "https://test.webhook.office.com/test")
    
    # Mock successful HTTP response
    with patch('src.main.requests.post') as mock_post:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        # Issue title with special characters
        issue_title = 'Fix "token counter" with <special> & characters'
        
        # Call function
        result = send_teams_notification(
            owner="testowner",
            repo="testrepo",
            issue_number=123,
            issue_title=issue_title,
            issue_url="https://github.com/testowner/testrepo/issues/123",
            comment_url="https://github.com/testowner/testrepo/issues/123#issuecomment-456"
        )
        
        # Should succeed
        assert result is True
        
        # Verify title is in payload
        payload = mock_post.call_args[1]["json"]
        card = payload["attachments"][0]["content"]
        issue_text = card["body"][1]["items"][0]["text"]
        assert issue_title in issue_text
