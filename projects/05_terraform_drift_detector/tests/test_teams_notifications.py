"""Tests for Microsoft Teams notifications."""

from unittest.mock import Mock, patch
from src.integrations.teams_notifications import (
    get_severity_color,
    send_drift_issue_notification,
    send_drift_summary_notification,
)


def test_get_severity_color():
    """Test severity to color mapping."""
    assert get_severity_color("CRITICAL") == "Attention"
    assert get_severity_color("HIGH") == "Warning"
    assert get_severity_color("MEDIUM") == "Accent"
    assert get_severity_color("LOW") == "Good"
    assert get_severity_color("critical") == "Attention"  # Case insensitive
    assert get_severity_color("UNKNOWN") == "Default"  # Fallback


@patch("src.integrations.teams_notifications.requests.post")
def test_send_drift_issue_notification_success(mock_post):
    """Test successful Teams notification for drift issue."""
    # Mock successful webhook response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "1"  # Teams webhook returns "1" on success
    mock_post.return_value = mock_response
    
    # Call function
    result = send_drift_issue_notification(
        issue_url="https://github.com/test/repo/issues/42",
        issue_number=42,
        title="Drift detected in web-prod-01",
        severity="CRITICAL",
        resource_count=3,
        workspace="production",
        webhook_url="https://test.webhook.office.com/test"
    )
    
    # Verify result
    assert result is True
    
    # Verify webhook call
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    
    # Verify webhook URL
    assert call_args[0][0] == "https://test.webhook.office.com/test"
    
    # Verify adaptive card structure
    card_data = call_args[1]["json"]
    assert card_data["type"] == "message"
    assert len(card_data["attachments"]) == 1
    
    # Verify card content
    card_content = card_data["attachments"][0]["content"]
    assert card_content["type"] == "AdaptiveCard"
    assert card_content["body"][0]["style"] == "Attention"  # CRITICAL = Red
    
    # Verify facts
    facts = card_content["body"][1]["facts"]
    fact_values = {fact["title"]: fact["value"] for fact in facts}
    assert fact_values["Workspace:"] == "production"
    assert fact_values["Severity:"] == "CRITICAL"
    assert fact_values["Resources:"] == "3"
    assert fact_values["Issue:"] == "#42"
    
    # Verify action button
    actions = card_content["actions"]
    assert len(actions) == 1
    assert actions[0]["title"] == "View Issue on GitHub"
    assert actions[0]["url"] == "https://github.com/test/repo/issues/42"


@patch("src.integrations.teams_notifications.requests.post")
def test_send_drift_issue_notification_retry(mock_post):
    """Test Teams notification retry logic."""
    # Mock timeout on first attempt, success on second
    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.text = "1"
    
    mock_post.side_effect = [
        Exception("Timeout"),  # First attempt fails
        mock_response_success,  # Second attempt succeeds
    ]
    
    # Call function
    result = send_drift_issue_notification(
        issue_url="https://github.com/test/repo/issues/42",
        issue_number=42,
        title="Test",
        severity="HIGH",
        resource_count=1,
        workspace="dev",
        webhook_url="https://test.webhook.office.com/test",
        max_retries=3
    )
    
    # Verify result (should succeed on retry)
    assert result is True
    assert mock_post.call_count == 2


@patch("src.integrations.teams_notifications.requests.post")
def test_send_drift_issue_notification_failure(mock_post):
    """Test Teams notification complete failure."""
    # Mock failure on all attempts
    mock_post.side_effect = Exception("Connection error")
    
    # Call function
    result = send_drift_issue_notification(
        issue_url="https://github.com/test/repo/issues/42",
        issue_number=42,
        title="Test",
        severity="MEDIUM",
        resource_count=1,
        workspace="staging",
        webhook_url="https://invalid.webhook.url",
        max_retries=2
    )
    
    # Verify result
    assert result is False
    assert mock_post.call_count == 2  # Retried twice


@patch("src.integrations.teams_notifications.requests.post")
def test_send_drift_summary_notification(mock_post):
    """Test Teams summary notification with drift statistics."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "1"
    mock_post.return_value = mock_response
    
    # Prepare test data
    drift_summary = {
        "total_resources": 15,
        "drifted": 4,
        "compliant": 11,
        "severity_breakdown": {
            "CRITICAL": 1,
            "HIGH": 2,
            "MEDIUM": 1,
            "LOW": 0,
        },
    }
    
    issues_created = [
        "https://github.com/test/repo/issues/1",
        "https://github.com/test/repo/issues/2",
        "https://github.com/test/repo/issues/3",
    ]
    
    # Call function
    result = send_drift_summary_notification(
        owner="test-owner",
        repo="test-repo",
        workspace="production",
        drift_summary=drift_summary,
        issues_created=issues_created,
        webhook_url="https://test.webhook.office.com/test"
    )
    
    # Verify result
    assert result is True
    
    # Verify webhook call
    mock_post.assert_called_once()
    call_args = mock_post.call_args
    
    # Verify adaptive card
    card_data = call_args[1]["json"]
    card_content = card_data["attachments"][0]["content"]
    
    # Should use red (Attention) color for CRITICAL severity
    assert card_content["body"][0]["style"] == "Attention"
    
    # Verify facts include all statistics
    facts = card_content["body"][1]["facts"]
    fact_values = {fact["title"]: fact["value"] for fact in facts}
    
    assert fact_values["Total Resources:"] == "15"
    assert fact_values["Drifted:"] == "4"
    assert fact_values["Compliant:"] == "11"
    assert fact_values["CRITICAL:"] == "1"
    assert fact_values["HIGH:"] == "2"
    assert fact_values["MEDIUM:"] == "1"
    assert fact_values["Issues Created:"] == "3"
    
    # Verify action buttons (limited to 3)
    actions = card_content["actions"]
    assert len(actions) == 3
    assert actions[0]["url"] == "https://github.com/test/repo/issues/1"


@patch("src.integrations.teams_notifications.requests.post")
def test_send_drift_summary_notification_no_drift(mock_post):
    """Test Teams summary notification with no drift (all compliant)."""
    # Mock successful response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = "1"
    mock_post.return_value = mock_response
    
    # Prepare test data - all compliant
    drift_summary = {
        "total_resources": 10,
        "drifted": 0,
        "compliant": 10,
        "severity_breakdown": {},
    }
    
    # Call function
    result = send_drift_summary_notification(
        owner="test-owner",
        repo="test-repo",
        workspace="production",
        drift_summary=drift_summary,
        issues_created=[],
        webhook_url="https://test.webhook.office.com/test"
    )
    
    # Verify result
    assert result is True
    
    # Verify card uses green (Good) color when no drift
    card_data = mock_post.call_args[1]["json"]
    card_content = card_data["attachments"][0]["content"]
    assert card_content["body"][0]["style"] == "Good"
