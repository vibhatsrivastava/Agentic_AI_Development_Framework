"""GitHub API integration tools for issue creation and management."""

import json
import requests
from typing import Optional, List, Dict, Set
from common.utils import get_logger, require_env

logger = get_logger(__name__)


def _matches_existing_drift_issue(issue: Dict, resource_id: str, drift_type: Optional[str] = None) -> bool:
    """Return True when an open issue already tracks the same drifted resource."""
    title = (issue.get("title") or "").lower()
    body = (issue.get("body") or "").lower()
    resource_id_lower = (resource_id or "").lower()
    drift_type_lower = (drift_type or "").lower()

    if resource_id_lower and resource_id_lower not in title and resource_id_lower not in body:
        return False

    if drift_type_lower and drift_type_lower not in title and drift_type_lower not in body:
        return False

    return True


def _get_existing_repo_labels(owner: str, repo: str, headers: Dict[str, str]) -> Set[str]:
    """Best-effort fetch of existing repository labels for payload validation."""
    try:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/labels",
            headers=headers,
            params={"per_page": 100},
            timeout=10,
        )
        resp.raise_for_status()
        labels = resp.json()
        if isinstance(labels, list):
            return {label.get("name") for label in labels if isinstance(label, dict) and label.get("name")}
    except Exception as e:
        logger.warning(f"Could not fetch repo labels for validation: {e}")
    return set()


def _filter_valid_assignees(
    owner: str,
    repo: str,
    assignees: Optional[List[str]],
    headers: Dict[str, str],
) -> List[str]:
    """Keep only assignees that are assignable for the target repository."""
    if not assignees:
        return []

    valid_assignees: List[str] = []
    for raw in assignees:
        username = raw.lstrip("@")
        if not username:
            continue

        try:
            resp = requests.get(
                f"https://api.github.com/repos/{owner}/{repo}/assignees/{username}",
                headers=headers,
                timeout=10,
            )
            if resp.status_code == 204:
                valid_assignees.append(username)
            else:
                logger.warning(
                    f"Skipping invalid assignee '{raw}' for {owner}/{repo} (status={resp.status_code})"
                )
        except Exception as e:
            logger.warning(f"Assignee validation failed for '{raw}': {e}. Skipping assignee.")

    return valid_assignees


def get_github_headers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Get GitHub API headers with authentication.
    
    Args:
        token: GitHub personal access token (uses GITHUB_TOKEN env var if not provided)
    
    Returns:
        Dictionary of headers for GitHub API requests
    """
    if token is None:
        token = require_env("GITHUB_TOKEN")
    
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def create_github_issue(
    owner: str,
    repo: str,
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    token: Optional[str] = None
) -> str:
    """
    Create a new GitHub issue with metadata.
    
    Args:
        owner: Repository owner (e.g., "vibhatsrivastava")
        repo: Repository name (e.g., "infrastructure-state")
        title: Issue title
        body: Issue body (markdown supported)
        labels: List of label names to apply
        assignees: List of GitHub usernames to assign (with or without @ prefix)
        token: GitHub personal access token (uses GITHUB_TOKEN env var if not provided)
    
    Returns:
        JSON string with issue details (number, url, created_at) or error message
    """
    try:
        headers = get_github_headers(token)

        # Validate labels against repository labels to avoid 422 on unknown labels.
        if labels:
            existing_labels = _get_existing_repo_labels(owner, repo, headers)
            if existing_labels:
                filtered_labels = [label for label in labels if label in existing_labels]
                dropped_labels = [label for label in labels if label not in existing_labels]
                for dropped in dropped_labels:
                    logger.warning(f"Skipping unknown label '{dropped}' for {owner}/{repo}")
                labels = filtered_labels

        # Validate assignees against GitHub assignability for this repository.
        assignees = _filter_valid_assignees(owner, repo, assignees, headers)
        
        payload = {
            "title": title,
            "body": body,
        }
        
        if labels:
            payload["labels"] = labels
        if assignees:
            payload["assignees"] = assignees
        
        logger.info(f"Creating GitHub issue in {owner}/{repo}: {title}")
        resp = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        
        logger.info(f"Successfully created issue #{result['number']}: {result['html_url']}")
        return json.dumps({
            "success": True,
            "issue_number": result["number"],
            "issue_url": result["html_url"],
            "created_at": result.get("created_at"),
        }, indent=2)
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"GitHub API error: {e.response.status_code} - {e.response.reason}"
        if e.response.status_code == 401:
            error_msg += ". Invalid GITHUB_TOKEN or token expired."
        elif e.response.status_code == 403:
            error_msg += ". Insufficient permissions. Ensure GITHUB_TOKEN has 'repo' scope."
        elif e.response.status_code == 404:
            error_msg += f". Repository {owner}/{repo} not found or inaccessible."
        elif e.response.status_code == 422:
            error_msg += ". Validation failed. Check assignees exist and labels are valid."
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        error_msg = f"Error creating GitHub issue: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})


def search_existing_issues(
    owner: str,
    repo: str,
    resource_id: str,
    drift_type: Optional[str] = None,
    token: Optional[str] = None
) -> str:
    """
    Search for existing open issues for a specific resource (deduplication).
    
    Args:
        owner: Repository owner
        repo: Repository name
        resource_id: AWS resource ID (e.g., "i-0123456789abcdef0")
        drift_type: Optional drift type filter (e.g., "Tags Modified")
        token: GitHub personal access token
    
    Returns:
        JSON string with search results: {"found": bool, "issue_number": int, "issue_url": str}
    """
    search_error = None
    try:
        headers = get_github_headers(token)
        
        # Build search query
        # Example: repo:owner/repo is:open label:infrastructure-drift "i-0123456789abcdef0" in:body
        query_parts = [
            f"repo:{owner}/{repo}",
            "is:open",
            "label:infrastructure-drift",
            f'"{resource_id}" in:body',
        ]
        
        if drift_type:
            query_parts.append(f'"{drift_type}" in:title')
        
        query = " ".join(query_parts)
        
        logger.info(f"Searching for existing issues: {query}")
        resp = requests.get(
            "https://api.github.com/search/issues",
            headers=headers,
            params={"q": query, "per_page": 1},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        
        if result["total_count"] > 0:
            issue = result["items"][0]
            logger.info(f"Found existing issue #{issue['number']}: {issue['html_url']}")
            return json.dumps({
                "found": True,
                "count": result.get("total_count", 0),
                "issue_number": issue["number"],
                "issue_url": issue["html_url"],
                "issue_title": issue["title"],
            }, indent=2)
        else:
            logger.info("No existing issue found via GitHub search API, checking recent open drift issues directly")
        
    except requests.exceptions.HTTPError as e:
        search_error = f"GitHub API error: {e.response.status_code} - {e.response.reason}"
        logger.warning(f"Search API lookup failed, falling back to issue list scan: {search_error}")
    except Exception as e:
        search_error = f"Error searching GitHub issues: {str(e)}"
        logger.warning(f"Search API lookup failed, falling back to issue list scan: {search_error}")

    try:
        resp = requests.get(
            f"https://api.github.com/repos/{owner}/{repo}/issues",
            headers=headers,
            params={
                "state": "open",
                "labels": "infrastructure-drift",
                "per_page": 100,
            },
            timeout=10,
        )
        resp.raise_for_status()

        for issue in resp.json():
            if not isinstance(issue, dict):
                continue
            if _matches_existing_drift_issue(issue, resource_id, drift_type):
                logger.info(
                    "Found existing issue via repository issue scan #%s: %s",
                    issue.get("number"),
                    issue.get("html_url"),
                )
                return json.dumps({
                    "found": True,
                    "count": 1,
                    "issue_number": issue.get("number"),
                    "issue_url": issue.get("html_url"),
                    "issue_title": issue.get("title"),
                }, indent=2)

        logger.info("No existing issue found")
        result = {"found": False, "count": 0}
        if search_error:
            result["search_error"] = search_error
        return json.dumps(result, indent=2)

    except requests.exceptions.HTTPError as e:
        error_msg = f"GitHub API error: {e.response.status_code} - {e.response.reason}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg, "found": False})
    except Exception as e:
        error_msg = f"Error searching GitHub issues: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg, "found": False})


def update_issue_labels(
    owner: str,
    repo: str,
    issue_number: int,
    add_labels: Optional[List[str]] = None,
    remove_labels: Optional[List[str]] = None,
    token: Optional[str] = None
) -> str:
    """
    Add or remove labels from a GitHub issue.
    
    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        add_labels: List of labels to add
        remove_labels: List of labels to remove
        token: GitHub personal access token
    
    Returns:
        JSON string with success status
    """
    try:
        headers = get_github_headers(token)
        base_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        
        # Add labels
        if add_labels:
            logger.info(f"Adding labels to issue #{issue_number}: {add_labels}")
            resp = requests.post(
                f"{base_url}/labels",
                headers=headers,
                json={"labels": add_labels},
                timeout=10,
            )
            resp.raise_for_status()
        
        # Remove labels
        if remove_labels:
            for label in remove_labels:
                logger.info(f"Removing label '{label}' from issue #{issue_number}")
                resp = requests.delete(
                    f"{base_url}/labels/{label}",
                    headers=headers,
                    timeout=10,
                )
                # 404 is OK (label doesn't exist on issue)
                if resp.status_code not in (200, 204, 404):
                    resp.raise_for_status()
        
        logger.info(f"Successfully updated labels for issue #{issue_number}")
        return json.dumps({"success": True, "issue_number": issue_number}, indent=2)
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"GitHub API error: {e.response.status_code} - {e.response.reason}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        error_msg = f"Error updating issue labels: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})


def close_issue(
    owner: str,
    repo: str,
    issue_number: int,
    comment: Optional[str] = None,
    token: Optional[str] = None
) -> str:
    """
    Close a GitHub issue with an optional final comment.
    
    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        comment: Optional comment to post before closing
        token: GitHub personal access token
    
    Returns:
        JSON string with success status
    """
    try:
        headers = get_github_headers(token)
        base_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        
        # Post comment if provided
        if comment:
            logger.info(f"Posting final comment to issue #{issue_number}")
            resp = requests.post(
                f"{base_url}/comments",
                headers=headers,
                json={"body": comment},
                timeout=10,
            )
            resp.raise_for_status()
        
        # Close issue
        logger.info(f"Closing issue #{issue_number}")
        resp = requests.patch(
            base_url,
            headers=headers,
            json={"state": "closed"},
            timeout=10,
        )
        resp.raise_for_status()
        
        logger.info(f"Successfully closed issue #{issue_number}")
        return json.dumps({
            "success": True,
            "issue_number": issue_number,
            "state": "closed",
        }, indent=2)
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"GitHub API error: {e.response.status_code} - {e.response.reason}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        error_msg = f"Error closing issue: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})


def post_issue_comment(
    owner: str,
    repo: str,
    issue_number: int,
    comment: str,
    token: Optional[str] = None
) -> str:
    """
    Post a comment to a GitHub issue.
    
    Args:
        owner: Repository owner
        repo: Repository name
        issue_number: Issue number
        comment: Comment body (markdown supported)
        token: GitHub personal access token
    
    Returns:
        JSON string with comment details (id, url, created_at) or error message
    """
    try:
        headers = get_github_headers(token)
        
        logger.info(f"Posting comment to issue #{issue_number} in {owner}/{repo}")
        resp = requests.post(
            f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments",
            headers=headers,
            json={"body": comment},
            timeout=10,
        )
        resp.raise_for_status()
        result = resp.json()
        
        logger.info(f"Successfully posted comment (ID: {result['id']})")
        return json.dumps({
            "success": True,
            "comment_id": result["id"],
            "comment_url": result.get("html_url"),
            "created_at": result.get("created_at"),
        }, indent=2)
        
    except requests.exceptions.HTTPError as e:
        error_msg = f"GitHub API error: {e.response.status_code} - {e.response.reason}"
        if e.response.status_code == 404:
            error_msg += f". Issue #{issue_number} not found."
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})
    except Exception as e:
        error_msg = f"Error posting comment: {str(e)}"
        logger.error(error_msg)
        return json.dumps({"success": False, "error": error_msg})
