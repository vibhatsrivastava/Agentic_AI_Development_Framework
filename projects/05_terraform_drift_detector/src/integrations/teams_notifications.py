"""Microsoft Teams notifications via adaptive cards for drift detection."""

import requests
import time
from datetime import datetime
from typing import Dict, Any
from common.utils import get_logger

logger = get_logger(__name__)


def get_severity_color(severity: str) -> str:
    """
    Get color code for severity level.
    
    Args:
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
    
    Returns:
        Hex color code for adaptive card
    """
    severity = severity.upper()
    colors = {
        "CRITICAL": "Attention",  # Red
        "HIGH": "Warning",        # Orange
        "MEDIUM": "Accent",       # Blue
        "LOW": "Good",            # Green
    }
    return colors.get(severity, "Default")


def send_drift_issue_notification(
    issue_url: str,
    issue_number: int,
    title: str,
    severity: str,
    resource_count: int,
    workspace: str,
    webhook_url: str,
    max_retries: int = 3
) -> bool:
    """
    Send Microsoft Teams notification for new drift issue.
    
    Args:
        issue_url: GitHub issue URL
        issue_number: GitHub issue number
        title: Issue title
        severity: Drift severity level (CRITICAL, HIGH, MEDIUM, LOW)
        resource_count: Number of drifted resources
        workspace: Terraform workspace name
        webhook_url: Microsoft Teams incoming webhook URL
        max_retries: Maximum number of retry attempts
    
    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        # Build adaptive card
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "Container",
                                "style": get_severity_color(severity),
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "🚨 Infrastructure Drift Detected",
                                        "weight": "Bolder",
                                        "size": "Large",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "FactSet",
                                "facts": [
                                    {
                                        "title": "Workspace:",
                                        "value": workspace
                                    },
                                    {
                                        "title": "Severity:",
                                        "value": severity.upper()
                                    },
                                    {
                                        "title": "Resources:",
                                        "value": str(resource_count)
                                    },
                                    {
                                        "title": "Issue:",
                                        "value": f"#{issue_number}"
                                    },
                                    {
                                        "title": "Detected:",
                                        "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
                                    }
                                ]
                            },
                            {
                                "type": "TextBlock",
                                "text": title,
                                "wrap": True,
                                "spacing": "Medium"
                            }
                        ],
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "View Issue on GitHub",
                                "url": issue_url
                            }
                        ]
                    }
                }
            ]
        }
        
        # Send with retry logic
        for attempt in range(max_retries):
            try:
                logger.info(f"Sending Teams notification (attempt {attempt + 1}/{max_retries})")
                resp = requests.post(
                    webhook_url,
                    headers={"Content-Type": "application/json"},
                    json=card,
                    timeout=10
                )
                resp.raise_for_status()

                # Teams webhook returns "1" on success
                if resp.text.strip() == "1":
                    logger.info(f"Successfully sent Teams notification for issue #{issue_number}")
                    return True

                logger.warning(f"Teams webhook returned unexpected response: {resp.text}")

            except requests.exceptions.Timeout:
                logger.warning(f"Teams webhook timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
            except requests.exceptions.HTTPError as e:
                logger.error(f"Teams webhook HTTP error: {e.response.status_code} - {e.response.reason}")
                if e.response.status_code == 429:
                    if attempt < max_retries - 1:
                        time.sleep(60)  # Wait 1 minute before retry
                    else:
                        break
                else:
                    break  # Don't retry on non-rate-limit HTTP errors
            except requests.exceptions.RequestException as e:
                logger.error(f"Teams webhook request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
            except Exception as e:
                logger.error(f"Unexpected error sending Teams notification: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        logger.error(f"Failed to send Teams notification after {max_retries} attempts")
        return False

    except Exception as e:
        logger.error(f"Unexpected error preparing Teams notification: {e}")
        return False


def send_drift_summary_notification(
    owner: str,
    repo: str,
    workspace: str,
    drift_summary: Dict[str, Any],
    issues_created: list,
    webhook_url: str
) -> bool:
    """
    Send Microsoft Teams summary notification for drift detection run.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        workspace: Terraform workspace name
        drift_summary: Dictionary with drift statistics
        issues_created: List of created issue URLs
        webhook_url: Microsoft Teams incoming webhook URL
    
    Returns:
        True if notification sent successfully, False otherwise
    """
    try:
        total_resources = drift_summary.get("total_resources", 0)
        drifted = drift_summary.get("drifted", 0)
        compliant = drift_summary.get("compliant", 0)
        severity_breakdown = drift_summary.get("severity_breakdown", {})
        
        # Determine overall severity color
        if severity_breakdown.get("CRITICAL", 0) > 0:
            color = "Attention"  # Red
        elif severity_breakdown.get("HIGH", 0) > 0:
            color = "Warning"  # Orange
        elif drifted > 0:
            color = "Accent"  # Blue
        else:
            color = "Good"  # Green
        
        # Build fact set
        facts = [
            {"title": "Workspace:", "value": workspace},
            {"title": "Repository:", "value": f"{owner}/{repo}"},
            {"title": "Total Resources:", "value": str(total_resources)},
            {"title": "Drifted:", "value": str(drifted)},
            {"title": "Compliant:", "value": str(compliant)},
        ]
        
        # Add severity breakdown
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            count = severity_breakdown.get(severity, 0)
            if count > 0:
                facts.append({"title": f"{severity}:", "value": str(count)})
        
        facts.append({
            "title": "Issues Created:",
            "value": str(len(issues_created))
        })
        facts.append({
            "title": "Scan Time:",
            "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        })
        
        # Build adaptive card
        card = {
            "type": "message",
            "attachments": [
                {
                    "contentType": "application/vnd.microsoft.card.adaptive",
                    "contentUrl": None,
                    "content": {
                        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                        "type": "AdaptiveCard",
                        "version": "1.4",
                        "body": [
                            {
                                "type": "Container",
                                "style": color,
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "📊 Drift Detection Summary",
                                        "weight": "Bolder",
                                        "size": "Large",
                                        "wrap": True
                                    }
                                ]
                            },
                            {
                                "type": "FactSet",
                                "facts": facts
                            }
                        ],
                        "actions": []
                    }
                }
            ]
        }
        
        # Add action buttons for each issue
        actions = card["attachments"][0]["content"]["actions"]
        for idx, issue_url in enumerate(issues_created[:3]):  # Limit to 3 buttons
            actions.append({
                "type": "Action.OpenUrl",
                "title": f"View Issue #{idx + 1}",
                "url": issue_url
            })
        
        # Send notification
        logger.info("Sending Teams drift summary notification")
        resp = requests.post(
            webhook_url,
            headers={"Content-Type": "application/json"},
            json=card,
            timeout=10
        )
        resp.raise_for_status()
        
        if resp.text.strip() == "1":
            logger.info("Successfully sent Teams summary notification")
            return True
        else:
            logger.warning(f"Teams webhook returned unexpected response: {resp.text}")
            return False
        
    except requests.exceptions.HTTPError as e:
        logger.error(f"Teams webhook HTTP error: {e.response.status_code} - {e.response.reason}")
        return False
    except Exception as e:
        logger.error(f"Error sending Teams summary notification: {e}")
        return False
