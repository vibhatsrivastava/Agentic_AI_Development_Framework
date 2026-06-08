"""
Configuration utilities for the Terraform Drift Analyzer Dashboard
"""

import os
from typing import Optional


class DashboardConfig:
    """Dashboard configuration loaded from environment variables."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # GitHub configuration
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.github_repo_owner = os.getenv("GITHUB_REPO_OWNER", "")
        self.github_repo_name = os.getenv("GITHUB_REPO_NAME", "")
        
        # Webhook configuration
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        self.webhook_port = int(os.getenv("WEBHOOK_PORT", "5000"))
        self.enable_webhook = os.getenv("ENABLE_WEBHOOK", "false").lower() == "true"
        
        # Streamlit configuration
        self.refresh_interval = int(os.getenv("DASHBOARD_REFRESH_INTERVAL", "60"))
        self.page_size = int(os.getenv("DASHBOARD_PAGE_SIZE", "50"))
        
        # Debug mode
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        
        self._validate()
    
    def _validate(self):
        """Validate required configuration."""
        if not self.github_token:
            raise ValueError("GITHUB_TOKEN environment variable is required")
        
        if not self.github_repo_owner or not self.github_repo_name:
            raise ValueError(
                "GITHUB_REPO_OWNER and GITHUB_REPO_NAME environment variables are required"
            )
    
    def is_webhook_enabled(self) -> bool:
        """Check if webhook integration is enabled."""
        return self.enable_webhook and bool(self.webhook_secret)
    
    def get_github_url(self) -> str:
        """Get GitHub repository URL."""
        return f"https://github.com/{self.github_repo_owner}/{self.github_repo_name}"
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary (excluding sensitive data)."""
        return {
            "github_repo_owner": self.github_repo_owner,
            "github_repo_name": self.github_repo_name,
            "github_token_configured": bool(self.github_token),
            "webhook_enabled": self.is_webhook_enabled(),
            "webhook_port": self.webhook_port,
            "refresh_interval": self.refresh_interval,
            "page_size": self.page_size,
            "debug": self.debug,
        }
