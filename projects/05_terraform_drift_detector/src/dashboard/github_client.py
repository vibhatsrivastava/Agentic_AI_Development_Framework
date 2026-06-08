"""
GitHub Integration Layer for Drift Dashboard

Handles GitHub API interactions, issue retrieval, parsing, and webhook validation.
"""

import os
import hmac
import hashlib
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import requests
from github import Github, GithubException


class DriftGitHubClient:
    """Client for retrieving and parsing Terraform drift issues from GitHub."""
    
    def __init__(self, token: Optional[str] = None):
        """
        Initialize GitHub client.
        
        Args:
            token: GitHub access token. If not provided, uses GITHUB_TOKEN env var.
        """
        self.token = token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            raise ValueError("GITHUB_TOKEN environment variable not set")
        
        self.github = Github(self.token)
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
    
    def get_drift_issues(self, repo_owner: str, repo_name: str, 
                        state: str = "open") -> List[Dict]:
        """
        Retrieve drift issues from GitHub repository.
        
        Args:
            repo_owner: Repository owner
            repo_name: Repository name
            state: Issue state ('open', 'closed', or 'all')
        
        Returns:
            List of drift record dictionaries
        """
        try:
            repo = self.github.get_user(repo_owner).get_repo(repo_name)
            # Look for both 'terraform-drift' and 'infrastructure-drift' labels
            issues_terraform = repo.get_issues(state=state, labels=["terraform-drift"])
            issues_infra = repo.get_issues(state=state, labels=["infrastructure-drift"])
            
            # Combine issues (avoiding duplicates)
            seen_numbers = set()
            all_issues = []
            
            for issue in issues_terraform:
                if issue.number not in seen_numbers:
                    all_issues.append(issue)
                    seen_numbers.add(issue.number)
            
            for issue in issues_infra:
                if issue.number not in seen_numbers:
                    all_issues.append(issue)
                    seen_numbers.add(issue.number)
            
            drift_records = []
            for issue in all_issues:
                drift_record = self._parse_issue_to_drift(issue)
                if drift_record:
                    drift_records.append(drift_record)
            
            return drift_records
        except GithubException as e:
            print(f"Error retrieving issues: {e}")
            return []
    
    def _parse_issue_to_drift(self, issue) -> Optional[Dict]:
        """
        Parse GitHub issue into drift record.
        
        Supports multiple formats:
        1. Old format with "Field: value" pattern
        2. New format with backtick-delimited values (e.g., `value`)
        3. Title-based parsing for resource name and type
        
        Args:
            issue: GitHub Issue object
        
        Returns:
            Drift record dictionary or None if parsing fails
        """
        try:
            body = issue.body or ""
            labels = [label.name for label in issue.labels]
            title = issue.title or ""
            
            # Extract Drift ID from title or body (e.g., "Drift: aws_instance.drift_test")
            drift_id = self._extract_field(body, "Drift ID") or self._extract_from_title(title)
            
            # Extract resource info from backtick format or colon format
            resource_name = self._extract_backtick_field(body, "Resource Name") or self._extract_field(body, "Resource Name")
            resource_type = self._extract_backtick_field(body, "Resource Type") or self._extract_field(body, "Resource Type")
            
            # Fallback: extract from title if not found in body
            if not resource_name or not resource_type:
                title_resource = self._parse_title_for_resource(title)
                if not resource_name:
                    resource_name = title_resource.get("name")
                if not resource_type:
                    resource_type = title_resource.get("type")
            
            # Ensure we have a drift_id even if not explicitly stated
            if not drift_id and resource_name:
                drift_id = f"{resource_type}.{resource_name}" if resource_type else resource_name
            
            # Extract basic info from issue
            drift_record = {
                "drift_id": drift_id or f"drift-{issue.number}",
                "resource_name": resource_name or "",
                "resource_type": resource_type or "",
                "severity": self._extract_severity(labels),
                "drift_description": self._extract_drift_type(body) or issue.title or "",
                "detection_timestamp": self._parse_timestamp(
                    self._extract_backtick_field(body, "Detection Timestamp") or 
                    self._extract_field(body, "Detection Timestamp") or ""
                ) or issue.created_at.isoformat(),
                "github_issue_number": issue.number,
                "github_issue_status": "open" if issue.state == "open" else "closed",
                "github_issue_url": issue.html_url,
                "remediation_status": self._extract_remediation_status(labels),
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
            }
            
            return drift_record
        
        except Exception as e:
            print(f"Error parsing issue #{issue.number}: {e}")
            return None
    
    @staticmethod
    def _extract_field(body: str, field_name: str) -> Optional[str]:
        """Extract field value from issue body."""
        for line in body.split("\n"):
            if field_name in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
        return None
    
    @staticmethod
    def _extract_backtick_field(body: str, field_name: str) -> Optional[str]:
        """Extract field value from backtick-delimited format (e.g., Resource Name: `value`)."""
        for line in body.split("\n"):
            if field_name in line:
                # Extract content between backticks
                if "`" in line:
                    start = line.find("`")
                    end = line.find("`", start + 1)
                    if start != -1 and end != -1 and start < end:
                        return line[start+1:end].strip()
                # Fallback to colon-based extraction
                parts = line.split(":", 1)
                if len(parts) == 2:
                    value = parts[1].strip()
                    # Remove backticks if present
                    if value.startswith("`") and value.endswith("`"):
                        value = value[1:-1]
                    return value
        return None
    
    @staticmethod
    def _extract_from_title(title: str) -> Optional[str]:
        """Extract drift ID from issue title (e.g., 'Drift: aws_instance.drift_test - tags_modified')."""
        if "Drift:" in title:
            parts = title.split("Drift:", 1)
            if len(parts) == 2:
                # Extract the resource identifier (before the hyphen)
                drift_part = parts[1].strip().split(" - ")[0].strip()
                return drift_part if drift_part else None
        return None
    
    @staticmethod
    def _parse_title_for_resource(title: str) -> dict:
        """Parse title to extract resource type and name."""
        result: Dict[str, Optional[str]] = {"type": None, "name": None}
        
        if "Drift:" in title:
            # Format: "Drift: aws_instance.drift_test - tags_modified"
            parts = title.split("Drift:", 1)[1].split(" - ")[0].strip()
            if "." in parts:
                resource_type, resource_name = parts.split(".", 1)
                result["type"] = resource_type.strip()
                result["name"] = resource_name.strip()
        
        return result
    
    @staticmethod
    def _extract_drift_type(body: str) -> Optional[str]:
        """Extract drift type from body (e.g., 'tags_modified' from 'Type: tags_modified')."""
        for line in body.split("\n"):
            if "Type:" in line and "Resource Type:" not in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    return parts[1].strip()
        return None
    
    @staticmethod
    def _extract_severity(labels: List[str]) -> str:
        """
        Extract severity from issue labels.
        
        Expected labels: severity-critical, severity-high, severity-medium, severity-low
        """
        severity_map = {
            "severity-critical": "Critical",
            "severity-high": "High",
            "severity-medium": "Medium",
            "severity-low": "Low",
        }
        
        for label in labels:
            if label in severity_map:
                return severity_map[label]
        
        return "Medium"  # Default severity
    
    @staticmethod
    def _extract_remediation_status(labels: List[str]) -> str:
        """
        Extract remediation status from issue labels.
        
        Expected labels: status-detected, status-issue-created, status-notified, 
                        status-remediation-running, status-validation-running, status-resolved
        """
        status_map = {
            "status-detected": "DETECTED",
            "status-issue-created": "ISSUE_CREATED",
            "status-notified": "NOTIFIED",
            "status-remediation-running": "REMEDIATION_RUNNING",
            "status-validation-running": "VALIDATION_RUNNING",
            "status-resolved": "RESOLVED",
        }
        
        for label in labels:
            if label in status_map:
                return status_map[label]
        
        return "DETECTED"  # Default status
    
    @staticmethod
    def _parse_timestamp(timestamp_str: str) -> Optional[str]:
        """
        Parse timestamp string to ISO format.
        
        Args:
            timestamp_str: Timestamp string (various formats supported)
        
        Returns:
            ISO format timestamp or None if parsing fails
        """
        if not timestamp_str:
            return None
        
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d",
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        
        return None
    
    def validate_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Validate GitHub webhook signature.
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature header value
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            print("Warning: No webhook secret configured")
            return False
        
        expected_sig = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_sig)
    
    def parse_webhook_event(self, payload: Dict) -> Optional[Dict]:
        """
        Parse GitHub webhook event payload.
        
        Args:
            payload: Webhook event JSON payload
        
        Returns:
            Parsed event data or None if not a drift-related event
        """
        try:
            action = payload.get("action")
            issue = payload.get("issue", {})
            labels = [label.get("name") for label in issue.get("labels", [])]
            
            # Only process drift-related issues
            if "terraform-drift" not in labels:
                return None
            
            return {
                "action": action,
                "issue_number": issue.get("number"),
                "issue_title": issue.get("title"),
                "issue_state": issue.get("state"),
                "issue_url": issue.get("html_url"),
                "timestamp": datetime.now().isoformat(),
                "labels": labels,
            }
        
        except Exception as e:
            print(f"Error parsing webhook event: {e}")
            return None
