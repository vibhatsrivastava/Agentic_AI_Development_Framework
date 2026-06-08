"""
Terraform Drift Analyzer Dashboard

Main Streamlit application for monitoring drift detection and remediation activities.
"""

import sys
import os
from pathlib import Path
import threading
import time

# Add project root to Python path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file BEFORE importing modules that use them
from dotenv import load_dotenv
load_dotenv(project_root / ".env")

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from src.dashboard.github_client import DriftGitHubClient
from src.dashboard.models import DriftRecord, DriftRecordParser, DriftRecordAnalytics
from src.dashboard.webhook_server import WebhookServer, WebhookConfig


# Page Configuration
st.set_page_config(
    page_title="Terraform Drift Analyzer Dashboard",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .critical-severity {
        color: #ff3333;
        font-weight: bold;
    }
    .high-severity {
        color: #ff9933;
        font-weight: bold;
    }
    .medium-severity {
        color: #ffcc33;
        font-weight: bold;
    }
    .low-severity {
        color: #33cc33;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


class DashboardState:
    """Manages dashboard state and caching."""
    
    @staticmethod
    def get_drift_data():
        """Retrieve drift data from cache or fetch from GitHub."""
        if "drift_records" not in st.session_state:
            st.session_state.drift_records = []
            st.session_state.last_refresh = None
        
        return st.session_state.drift_records
    
    @staticmethod
    def update_drift_data(records: List[DriftRecord]):
        """Update cached drift data."""
        st.session_state.drift_records = records
        st.session_state.last_refresh = datetime.now()


class DashboardUI:
    """Streamlit UI components for the dashboard."""
    
    @staticmethod
    def render_header():
        """Render dashboard header."""
        st.title("🔄 Terraform Drift Analyzer Dashboard")
        st.markdown("Monitor infrastructure drift detection and remediation in real-time")
    
    @staticmethod
    def render_metrics(metrics: Dict):
        """Render summary metrics cards."""
        st.subheader("📊 Summary Metrics")
        
        cols = st.columns(5)
        
        with cols[0]:
            st.metric(
                label="Total Active",
                value=metrics["total_active"],
                delta=None,
                delta_color="inverse"
            )
        
        with cols[1]:
            st.metric(
                label="Total Resolved",
                value=metrics["total_resolved"],
                delta=None
            )
        
        with cols[2]:
            st.metric(
                label="Critical",
                value=metrics["critical_count"],
                delta=None,
                delta_color="inverse"
            )
        
        with cols[3]:
            st.metric(
                label="High Severity",
                value=metrics["high_count"],
                delta=None
            )
        
        with cols[4]:
            avg_time = metrics["avg_resolution_hours"]
            if avg_time:
                st.metric(
                    label="Avg Resolution",
                    value=f"{avg_time}h"
                )
            else:
                st.metric(
                    label="Avg Resolution",
                    value="N/A"
                )
        
        st.divider()
    
    @staticmethod
    def render_filter_sidebar() -> Dict:
        """Render filter sidebar and return filter selections."""
        st.sidebar.subheader("🔍 Filters")
        
        filters = {
            "status": st.sidebar.multiselect(
                "Drift Status",
                ["Active", "Resolved", "All"],
                default=["Active"]
            ),
            "severity": st.sidebar.multiselect(
                "Severity Level",
                ["Critical", "High", "Medium", "Low"],
                default=["Critical", "High"]
            ),
            "remediation_status": st.sidebar.multiselect(
                "Remediation Status",
                ["DETECTED", "ISSUE_CREATED", "NOTIFIED", "REMEDIATION_RUNNING", 
                 "VALIDATION_RUNNING", "RESOLVED"],
                default=[]
            ),
        }
        
        return filters
    
    @staticmethod
    def apply_filters(records: List[DriftRecord], filters: Dict) -> List[DriftRecord]:
        """Apply selected filters to drift records."""
        filtered = records
        
        # Status filter
        status_filter = filters.get("status", ["All"])
        if "Active" in status_filter and "Resolved" not in status_filter:
            filtered = [r for r in filtered if r.is_active()]
        elif "Resolved" in status_filter and "Active" not in status_filter:
            filtered = [r for r in filtered if r.is_resolved()]
        
        # Severity filter
        severity_filter = filters.get("severity", [])
        if severity_filter:
            filtered = [r for r in filtered if r.severity in severity_filter]
        
        # Remediation status filter
        remediation_filter = filters.get("remediation_status", [])
        if remediation_filter:
            filtered = [r for r in filtered if r.remediation_status in remediation_filter]
        
        return filtered
    
    @staticmethod
    def render_active_drift_table(records: List[DriftRecord]):
        """Render active drift records in a table."""
        st.subheader("🚨 Active Drift Issues")
        
        if not records:
            st.info("No active drift issues detected")
            return
        
        # Sort by severity
        records = DriftRecordAnalytics.sort_by_severity_desc(records)
        
        table_data = []
        for record in records:
            table_data.append({
                "Resource": f"{record.resource_name} ({record.resource_type})",
                "Severity": record.severity,
                "Status": record.remediation_status,
                "Detection Time": record.detection_timestamp,
                "Issue #": f"[#{record.github_issue_number}]({record.github_issue_url})",
                "Age": DashboardUI._calculate_age(record.detection_timestamp),
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.write(f"Total: {len(records)} active issues")
    
    @staticmethod
    def render_resolved_drift_table(records: List[DriftRecord]):
        """Render resolved drift records in a table."""
        st.subheader("✅ Resolved Drift Issues")
        
        if not records:
            st.info("No resolved drift issues")
            return
        
        # Sort by closure time
        records = sorted(records, key=lambda r: r.closed_at or "", reverse=True)
        
        table_data = []
        for record in records:
            duration = record.get_resolution_duration()
            table_data.append({
                "Resource": f"{record.resource_name} ({record.resource_type})",
                "Severity": record.severity,
                "Detection": record.detection_timestamp,
                "Resolved": record.closed_at if record.closed_at else "N/A",
                "Duration": duration or "N/A",
                "Issue #": f"[#{record.github_issue_number}]({record.github_issue_url})",
            })
        
        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.write(f"Total: {len(records)} resolved issues")
    
    @staticmethod
    def render_drift_details(record: DriftRecord):
        """Render detailed view for a single drift record."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {record.drift_id}")
            st.markdown(f"**Resource:** {record.resource_name}")
            st.markdown(f"**Type:** {record.resource_type}")
            st.markdown(f"**Severity:** {record.severity}")
        
        with col2:
            st.markdown(f"**Status:** {record.remediation_status}")
            st.markdown(f"**Issue:** [#{record.github_issue_number}]({record.github_issue_url})")
            st.markdown(f"**Detected:** {record.detection_timestamp}")
            if record.closed_at:
                st.markdown(f"**Resolved:** {record.closed_at}")
        
        st.divider()
        
        st.markdown("#### Description")
        st.markdown(record.drift_description)
        
        if record.get_resolution_duration():
            st.markdown(f"**Resolution Time:** {record.get_resolution_duration()}")
    
    @staticmethod
    def _calculate_age(timestamp: str) -> str:
        """Calculate and format time elapsed since timestamp."""
        try:
            detected = datetime.fromisoformat(timestamp)
            age = datetime.now() - detected
            
            if age.days > 0:
                return f"{age.days}d"
            else:
                hours = age.total_seconds() / 3600
                if hours > 0:
                    return f"{int(hours)}h"
                else:
                    minutes = age.total_seconds() / 60
                    return f"{int(minutes)}m"
        except (ValueError, TypeError):
            return "N/A"


# Initialize session state for webhook events
if "webhook_event" not in st.session_state:
    st.session_state.webhook_event = None
if "last_webhook_update" not in st.session_state:
    st.session_state.last_webhook_update = None
if "webhook_triggered_refresh" not in st.session_state:
    st.session_state.webhook_triggered_refresh = False


def fetch_drift_data(github_client: DriftGitHubClient, repo_owner: str, 
                     repo_name: str) -> List[DriftRecord]:
    """Fetch drift data from GitHub and return as DriftRecord objects."""
    try:
        # Fetch open issues
        open_issues = github_client.get_drift_issues(repo_owner, repo_name, state="open")
        
        # Fetch closed issues
        closed_issues = github_client.get_drift_issues(repo_owner, repo_name, state="closed")
        
        all_issues = open_issues + closed_issues
        
        records = []
        for issue in all_issues:
            if DriftRecordParser.validate_record(issue):
                record = DriftRecordParser.enrich_record(issue)
                records.append(record)
        
        return records
    except Exception as e:
        st.error(f"Error fetching drift data: {e}")
        return []


def main():
    """Main dashboard application."""
    
    # Initialize GitHub client
    try:
        github_client = DriftGitHubClient()
    except ValueError as e:
        st.error(f"Configuration Error: {e}")
        st.info("Please set the GITHUB_TOKEN environment variable")
        return
    
    # Initialize webhook server if enabled
    webhook_config = WebhookConfig()
    webhook_server = None
    webhook_thread = None
    webhook_status = "⚪ Disabled"
    webhook_port_display = ""
    
    if webhook_config.enable_webhook and webhook_config.is_valid():
        try:
            # Initialize webhook server
            webhook_server = WebhookServer(port=webhook_config.webhook_port, debug=False)
            
            # Register callback to refresh dashboard when webhook events arrive
            def on_webhook_event(event):
                """Callback triggered when GitHub webhook event is received."""
                print(f"[DASHBOARD] 🔄 Webhook callback triggered for issue #{event.get('issue_number')}")
                st.session_state.webhook_event = event
                st.session_state.last_webhook_update = datetime.now().isoformat()
                st.session_state.webhook_triggered_refresh = True  # Flag for rerun
                print(f"[DASHBOARD] ✅ Refresh flag set - dashboard will rerun on next check")
            
            webhook_server.register_refresh_callback(on_webhook_event)
            
            # Start webhook server in background thread
            webhook_thread = threading.Thread(
                target=webhook_server.run,
                daemon=True,
                name="WebhookServer"
            )
            webhook_thread.start()
            
            webhook_status = "🟢 Connected"
            webhook_port_display = f":{webhook_config.webhook_port}"
        except Exception as e:
            st.warning(f"Failed to start webhook server: {e}")
            webhook_status = "🔴 Error"
            webhook_port_display = ""
    
    # Get configuration
    repo_owner = os.getenv("GITHUB_REPO_OWNER", "")
    repo_name = os.getenv("GITHUB_REPO_NAME", "")
    
    if not repo_owner or not repo_name:
        st.error("Configuration Missing")
        st.info("Please set GITHUB_REPO_OWNER and GITHUB_REPO_NAME environment variables")
        return
    
    # Check if webhook event triggered a refresh and perform rerun
    if st.session_state.webhook_triggered_refresh:
        st.session_state.webhook_triggered_refresh = False
        st.rerun()
    
    # Render header
    DashboardUI.render_header()
    
    # Sidebar configuration
    st.sidebar.title("⚙️ Configuration")
    
    # Refresh interval setting
    refresh_interval = st.sidebar.slider(
        "Auto-refresh interval (seconds)",
        min_value=10,
        max_value=300,
        value=60,
        step=10
    )
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.rerun()
    
    # Webhook status indicator
    if webhook_config.enable_webhook:
        st.sidebar.markdown("---")
        st.sidebar.markdown("### 🔗 Webhook Status")
        st.sidebar.markdown(f"**Status:** {webhook_status}")
        if webhook_port_display:
            st.sidebar.markdown(f"**Port:** {webhook_port_display}")
        
        # Show last webhook event if received
        if "last_webhook_update" in st.session_state and st.session_state.last_webhook_update:
            last_update = st.session_state.get("last_webhook_update", "N/A")
            st.sidebar.caption(f"Last update: {last_update}")
        
        if "webhook_event" in st.session_state and st.session_state.webhook_event:
            event = st.session_state.webhook_event
            st.sidebar.info(
                f"✅ Event received:\n"
                f"**Action:** {event.get('action')}\n"
                f"**Issue:** #{event.get('issue_number')}\n"
                f"**Title:** {event.get('issue_title', 'N/A')[:50]}"
            )
    
    # Fetch data
    with st.spinner("Fetching drift data..."):
        records = fetch_drift_data(github_client, repo_owner, repo_name)
    
    if not records:
        st.warning("No drift records found. Make sure the repository has issues with 'terraform-drift' label.")
        return
    
    # Calculate metrics
    metrics = DriftRecordAnalytics.calculate_metrics(records)
    
    # Render metrics
    DashboardUI.render_metrics(metrics)
    
    # Render filters
    filters = DashboardUI.render_filter_sidebar()
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["Active Drifts", "Resolved Drifts"])
    
    with tab1:
        active_records = [r for r in records if r.is_active()]
        filtered_active = DashboardUI.apply_filters(active_records, filters)
        DashboardUI.render_active_drift_table(filtered_active)
    
    with tab2:
        resolved_records = [r for r in records if r.is_resolved()]
        filtered_resolved = DashboardUI.apply_filters(resolved_records, filters)
        DashboardUI.render_resolved_drift_table(filtered_resolved)
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"Repository: {repo_owner}/{repo_name}")
    
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col3:
        st.caption(f"Total records: {len(records)}")


if __name__ == "__main__":
    main()
