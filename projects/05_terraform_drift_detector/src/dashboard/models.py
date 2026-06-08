"""
Data Models and Utilities for Drift Records

Handles data structures and transformations for drift records.
"""

from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from enum import Enum


class Severity(str, Enum):
    """Severity levels for drift records."""
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class RemediationStatus(str, Enum):
    """Remediation lifecycle statuses."""
    DETECTED = "DETECTED"
    ISSUE_CREATED = "ISSUE_CREATED"
    NOTIFIED = "NOTIFIED"
    REMEDIATION_RUNNING = "REMEDIATION_RUNNING"
    VALIDATION_RUNNING = "VALIDATION_RUNNING"
    RESOLVED = "RESOLVED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"  # Future: HITL support


class IssueStatus(str, Enum):
    """GitHub issue status."""
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class DriftRecord:
    """Represents a Terraform drift record."""
    
    drift_id: str
    resource_name: str
    resource_type: str
    severity: str
    drift_description: str
    detection_timestamp: str
    github_issue_number: int
    github_issue_status: str
    github_issue_url: str
    remediation_status: str
    created_at: str
    updated_at: str
    closed_at: Optional[str] = None
    teams_notification_status: Optional[str] = None
    resolution_duration_minutes: Optional[int] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def is_active(self) -> bool:
        """Check if drift is active (not resolved)."""
        return self.github_issue_status == "open"
    
    def is_resolved(self) -> bool:
        """Check if drift is resolved."""
        return self.github_issue_status == "closed" or self.remediation_status == "RESOLVED"
    
    def get_severity_level(self) -> int:
        """Get numeric severity level for sorting (higher = more severe)."""
        severity_levels = {
            "Critical": 4,
            "High": 3,
            "Medium": 2,
            "Low": 1,
        }
        return severity_levels.get(self.severity, 0)
    
    def get_resolution_duration(self) -> Optional[str]:
        """Calculate and format resolution duration."""
        if not self.closed_at or not self.detection_timestamp:
            return None
        
        try:
            detected = datetime.fromisoformat(self.detection_timestamp)
            closed = datetime.fromisoformat(self.closed_at)
            duration = closed - detected
            
            hours = duration.total_seconds() / 3600
            if hours < 1:
                minutes = duration.total_seconds() / 60
                return f"{int(minutes)} minutes"
            elif hours < 24:
                return f"{int(hours)} hours"
            else:
                days = hours / 24
                return f"{int(days)} days"
        except (ValueError, TypeError):
            return None


class DriftRecordParser:
    """Utility for parsing and transforming drift records."""
    
    @staticmethod
    def validate_record(record: Dict) -> bool:
        """
        Validate drift record has required fields.
        
        Args:
            record: Dictionary with drift record data
        
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "drift_id",
            "resource_name",
            "resource_type",
            "severity",
            "drift_description",
            "detection_timestamp",
            "github_issue_number",
            "github_issue_status",
            "github_issue_url",
            "remediation_status",
        ]
        
        return all(field in record and record[field] for field in required_fields)
    
    @staticmethod
    def enrich_record(record: Dict) -> DriftRecord:
        """
        Enrich raw record with calculated fields.
        
        Args:
            record: Raw drift record dictionary
        
        Returns:
            Enriched DriftRecord object
        """
        return DriftRecord(
            drift_id=record.get("drift_id", ""),
            resource_name=record.get("resource_name", ""),
            resource_type=record.get("resource_type", ""),
            severity=record.get("severity", "Medium"),
            drift_description=record.get("drift_description", ""),
            detection_timestamp=record.get("detection_timestamp", ""),
            github_issue_number=record.get("github_issue_number", 0),
            github_issue_status=record.get("github_issue_status", "open"),
            github_issue_url=record.get("github_issue_url", ""),
            remediation_status=record.get("remediation_status", "DETECTED"),
            created_at=record.get("created_at", ""),
            updated_at=record.get("updated_at", ""),
            closed_at=record.get("closed_at"),
            teams_notification_status=record.get("teams_notification_status"),
        )


class DriftRecordAnalytics:
    """Analytics and aggregation for drift records."""
    
    @staticmethod
    def calculate_metrics(records: List[DriftRecord]) -> Dict:
        """
        Calculate summary metrics from drift records.
        
        Args:
            records: List of drift records
        
        Returns:
            Dictionary with metrics
        """
        active_records = [r for r in records if r.is_active()]
        resolved_records = [r for r in records if r.is_resolved()]
        
        critical_count = len([r for r in active_records if r.severity == "Critical"])
        high_count = len([r for r in active_records if r.severity == "High"])
        
        # Calculate average resolution time
        avg_resolution_minutes = None
        if resolved_records:
            total_minutes = 0
            valid_records = 0
            for record in resolved_records:
                if record.closed_at and record.detection_timestamp:
                    try:
                        detected = datetime.fromisoformat(record.detection_timestamp)
                        closed = datetime.fromisoformat(record.closed_at)
                        duration_minutes = (closed - detected).total_seconds() / 60
                        total_minutes += duration_minutes
                        valid_records += 1
                    except (ValueError, TypeError):
                        continue
            
            if valid_records > 0:
                avg_resolution_minutes = int(total_minutes / valid_records)
        
        return {
            "total_active": len(active_records),
            "total_resolved": len(resolved_records),
            "total_all": len(records),
            "critical_count": critical_count,
            "high_count": high_count,
            "avg_resolution_minutes": avg_resolution_minutes,
            "avg_resolution_hours": int(avg_resolution_minutes / 60) if avg_resolution_minutes else None,
        }
    
    @staticmethod
    def group_by_severity(records: List[DriftRecord]) -> Dict[str, List[DriftRecord]]:
        """
        Group drift records by severity.
        
        Args:
            records: List of drift records
        
        Returns:
            Dictionary with severity as key, list of records as value
        """
        groups = {
            "Critical": [],
            "High": [],
            "Medium": [],
            "Low": [],
        }
        
        for record in records:
            if record.severity in groups:
                groups[record.severity].append(record)
        
        return groups
    
    @staticmethod
    def group_by_status(records: List[DriftRecord]) -> Dict[str, List[DriftRecord]]:
        """
        Group drift records by remediation status.
        
        Args:
            records: List of drift records
        
        Returns:
            Dictionary with status as key, list of records as value
        """
        groups = {}
        for record in records:
            status = record.remediation_status
            if status not in groups:
                groups[status] = []
            groups[status].append(record)
        
        return groups
    
    @staticmethod
    def sort_by_severity_desc(records: List[DriftRecord]) -> List[DriftRecord]:
        """Sort records by severity (most critical first)."""
        return sorted(records, key=lambda r: r.get_severity_level(), reverse=True)
    
    @staticmethod
    def sort_by_detection_time_desc(records: List[DriftRecord]) -> List[DriftRecord]:
        """Sort records by detection timestamp (newest first)."""
        def get_timestamp(record):
            try:
                return datetime.fromisoformat(record.detection_timestamp)
            except (ValueError, TypeError):
                return datetime.min
        
        return sorted(records, key=get_timestamp, reverse=True)
