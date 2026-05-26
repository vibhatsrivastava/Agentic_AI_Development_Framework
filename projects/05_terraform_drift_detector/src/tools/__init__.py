"""Drift detection tools for Terraform resources."""

from .terraform_tools import parse_terraform_state
from .diff_tools import compare_resources
from .policy_tools import create_policy_analysis_tool

# Optional heavy imports: import lazily and tolerate missing optional deps during tests
try:
    from .aws_tools import fetch_cloud_resources
except Exception:
    fetch_cloud_resources = None

try:
    from .github_tools import (
        create_github_issue,
        search_existing_issues,
        update_issue_labels,
        close_issue,
        post_issue_comment,
    )
except Exception:
    create_github_issue = None
    search_existing_issues = None
    update_issue_labels = None
    close_issue = None
    post_issue_comment = None

__all__ = [
    "parse_terraform_state",
    "fetch_cloud_resources",
    "compare_resources",
    "create_policy_analysis_tool",
    "create_github_issue",
    "search_existing_issues",
    "update_issue_labels",
    "close_issue",
    "post_issue_comment",
]
