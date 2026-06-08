"""
Webhook Integration for Real-Time Dashboard Updates

Handles GitHub webhook events and automatic dashboard refresh.
"""

import os
from datetime import datetime
from typing import Optional, Dict, Callable
from flask import Flask, request, jsonify
import json
import logging
from src.dashboard.github_client import DriftGitHubClient


class WebhookServer:
    """Flask-based webhook server for GitHub events."""
    
    def __init__(self, port: int = 5000, debug: bool = False):
        """
        Initialize webhook server.
        
        Args:
            port: Port to listen on
            debug: Enable debug mode
        """
        self.app = Flask(__name__)
        self.port = port
        self.debug = debug
        self.github_client = DriftGitHubClient()
        self.refresh_callback: Optional[Callable] = None
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route("/health", methods=["GET"])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})
        
        @self.app.route("/webhook", methods=["POST"])
        def webhook():
            """GitHub webhook endpoint."""
            return self._handle_webhook(request)
    
    def _handle_webhook(self, req):
        """
        Handle GitHub webhook request.
        
        Args:
            req: Flask request object
        
        Returns:
            JSON response
        """
        try:
            # Validate webhook signature
            signature = req.headers.get("X-Hub-Signature-256", "")
            if not self.github_client.validate_webhook_signature(req.data, signature):
                self.logger.warning("Invalid webhook signature")
                return jsonify({"error": "Invalid signature"}), 401
            
            # Parse payload
            payload = req.get_json()
            event = self.github_client.parse_webhook_event(payload)
            
            if not event:
                return jsonify({"status": "ignored"}), 200
            
            # Log event
            self.logger.info(f"Webhook event received: {event['action']} for issue #{event['issue_number']}")
            
            # Trigger refresh callback if registered
            if self.refresh_callback:
                self.refresh_callback(event)
            
            return jsonify({"status": "processed", "event": event}), 200
        
        except Exception as e:
            self.logger.error(f"Error processing webhook: {e}")
            return jsonify({"error": str(e)}), 500
    
    def register_refresh_callback(self, callback: Callable):
        """
        Register callback to be called when webhook event is received.
        
        Args:
            callback: Function to call with event data
        """
        self.refresh_callback = callback
    
    def run(self):
        """Start webhook server."""
        self.logger.info(f"Starting webhook server on port {self.port}")
        self.app.run(host="0.0.0.0", port=self.port, debug=self.debug)


class WebhookEventCache:
    """Cache for recent webhook events to track dashboard refresh state."""
    
    def __init__(self, max_size: int = 100):
        """
        Initialize event cache.
        
        Args:
            max_size: Maximum number of events to cache
        """
        self.max_size = max_size
        self.events: Dict[str, Dict] = {}
        self.timestamps: Dict[str, datetime] = {}
    
    def add_event(self, event_id: str, event_data: Dict):
        """
        Add event to cache.
        
        Args:
            event_id: Unique event identifier
            event_data: Event data dictionary
        """
        self.events[event_id] = event_data
        self.timestamps[event_id] = datetime.now()
        
        # Enforce max size - remove oldest events
        if len(self.events) > self.max_size:
            oldest_id = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
            del self.events[oldest_id]
            del self.timestamps[oldest_id]
    
    def get_event(self, event_id: str) -> Optional[Dict]:
        """Get event from cache."""
        return self.events.get(event_id)
    
    def get_latest_events(self, limit: int = 10) -> list:
        """
        Get most recent events.
        
        Args:
            limit: Number of events to return
        
        Returns:
            List of events, ordered by timestamp descending
        """
        sorted_events = sorted(
            self.events.items(),
            key=lambda x: self.timestamps[x[0]],
            reverse=True
        )
        return [event for _, event in sorted_events[:limit]]
    
    def clear(self):
        """Clear all cached events."""
        self.events.clear()
        self.timestamps.clear()


class WebhookConfig:
    """Configuration for webhook integration."""
    
    def __init__(self):
        """Load configuration from environment variables."""
        self.webhook_port = int(os.getenv("WEBHOOK_PORT", "5000"))
        self.webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")
        self.repo_owner = os.getenv("GITHUB_REPO_OWNER", "")
        self.repo_name = os.getenv("GITHUB_REPO_NAME", "")
        self.enable_webhook = os.getenv("ENABLE_WEBHOOK", "false").lower() == "true"
        
        self._validate()
    
    def _validate(self):
        """Validate configuration."""
        if self.enable_webhook:
            if not self.webhook_secret:
                print("Warning: GITHUB_WEBHOOK_SECRET not set")
            if not self.repo_owner or not self.repo_name:
                raise ValueError("GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set when webhook is enabled")
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.repo_owner and self.repo_name)
