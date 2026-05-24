"""Tests for resource comparison and drift detection tools."""

import json
from tools.diff_tools import compare_resources


def test_compare_resources_no_drift():
    """Test comparison when state and cloud resources match perfectly."""
    state_resources = json.dumps({
        "total_resources": 1,
        "resources": [
            {
                "type": "aws_instance",
                "name": "web-prod-01",
                "id": "i-abc123",
                "tags": {"Environment": "prod", "Name": "web-prod-01"},
                "attributes": {"instance_type": "t3.medium"}
            }
        ]
    })
    
    cloud_resources = json.dumps({
        "resource_type": "aws_instance",
        "resources": [
            {
                "id": "i-abc123",
                "tags": {"Environment": "prod", "Name": "web-prod-01"},
                "attributes": {"instance_type": "t3.medium"}
            }
        ]
    })
    
    result_json = compare_resources.invoke({
        "state_resources": state_resources,
        "cloud_resources": cloud_resources
    })
    result = json.loads(result_json)
    
    assert result["total_drifted"] == 0
    assert len(result["drifted_resources"]) == 0


def test_compare_resources_tags_modified():
    """Test detection of modified tags."""
    state_resources = json.dumps({
        "resources": [
            {
                "type": "aws_instance",
                "name": "web-prod-01",
                "id": "i-abc123",
                "tags": {"Environment": "prod", "Name": "web-prod-01"},
                "attributes": {}
            }
        ]
    })
    
    cloud_resources = json.dumps({
        "resource_type": "aws_instance",
        "resources": [
            {
                "id": "i-abc123",
                "tags": {"Name": "web-prod-01-temp"},  # Environment tag removed, Name modified
                "attributes": {}
            }
        ]
    })
    
    result_json = compare_resources.invoke({
        "state_resources": state_resources,
        "cloud_resources": cloud_resources
    })
    result = json.loads(result_json)
    
    assert result["total_drifted"] == 1
    
    drift = result["drifted_resources"][0]
    assert drift["drift_type"] == "tags_modified"
    assert "Environment" in drift["changes"]["removed_tags"]
    assert "Name" in drift["changes"]["modified_tags"]


def test_compare_resources_attributes_changed():
    """Test detection of changed resource attributes."""
    state_resources = json.dumps({
        "resources": [
            {
                "type": "aws_instance",
                "name": "web-prod-01",
                "id": "i-abc123",
                "tags": {},
                "attributes": {"instance_type": "t3.medium"}
            }
        ]
    })
    
    cloud_resources = json.dumps({
        "resource_type": "aws_instance",
        "resources": [
            {
                "id": "i-abc123",
                "tags": {},
                "attributes": {"instance_type": "t3.large"}  # Instance type changed
            }
        ]
    })
    
    result_json = compare_resources.invoke({
        "state_resources": state_resources,
        "cloud_resources": cloud_resources
    })
    result = json.loads(result_json)
    
    assert result["total_drifted"] == 1
    
    drift = result["drifted_resources"][0]
    assert drift["drift_type"] == "attributes_changed"
    assert "instance_type" in drift["changes"]["modified_attributes"]


def test_compare_resources_resource_deleted():
    """Test detection of resources deleted outside Terraform."""
    state_resources = json.dumps({
        "resources": [
            {
                "type": "aws_instance",
                "name": "web-prod-01",
                "id": "i-abc123",
                "tags": {},
                "attributes": {}
            }
        ]
    })
    
    cloud_resources = json.dumps({
        "resource_type": "aws_instance",
        "resources": []  # Resource not found in cloud
    })
    
    result_json = compare_resources.invoke({
        "state_resources": state_resources,
        "cloud_resources": cloud_resources
    })
    result = json.loads(result_json)
    
    assert result["total_drifted"] == 1
    
    drift = result["drifted_resources"][0]
    assert drift["drift_type"] == "resource_deleted"
    assert drift["severity"] == "critical"


def test_compare_resources_resource_created():
    """Test detection of resources created outside Terraform."""
    state_resources = json.dumps({
        "resources": []  # No resources in state
    })
    
    cloud_resources = json.dumps({
        "resource_type": "aws_instance",
        "resources": [
            {
                "id": "i-xyz999",
                "tags": {},
                "attributes": {}
            }
        ]
    })
    
    result_json = compare_resources.invoke({
        "state_resources": state_resources,
        "cloud_resources": cloud_resources
    })
    result = json.loads(result_json)
    
    assert result["total_drifted"] == 1
    
    drift = result["drifted_resources"][0]
    assert drift["drift_type"] == "resource_created"
    assert drift["resource_id"] == "i-xyz999"


def test_compare_resources_invalid_json_input():
    """Test handling of invalid JSON input."""
    result_json = compare_resources.invoke({
        "state_resources": "{invalid json}",
        "cloud_resources": "{}"
    })
    result = json.loads(result_json)
    
    assert "error" in result


def test_compare_resources_error_from_previous_tool():
    """Test handling of error responses from previous tools."""
    state_resources = json.dumps({"error": "State parse failed"})
    cloud_resources = json.dumps({"resources": []})
    
    result_json = compare_resources.invoke({
        "state_resources": state_resources,
        "cloud_resources": cloud_resources
    })
    result = json.loads(result_json)
    
    assert "error" in result


def test_classify_tag_drift_severity_critical():
    """Test that critical tags (Environment, Backup) get critical severity."""
    from tools.diff_tools import _classify_tag_drift_severity
    
    tag_drift = {"removed_tags": ["Environment", "Backup"]}
    severity = _classify_tag_drift_severity(tag_drift)
    
    assert severity == "critical"


def test_classify_tag_drift_severity_high():
    """Test that high-priority tags (Owner, CostCenter) get high severity."""
    from tools.diff_tools import _classify_tag_drift_severity
    
    tag_drift = {"removed_tags": ["Owner"]}
    severity = _classify_tag_drift_severity(tag_drift)
    
    assert severity == "high"


def test_classify_attribute_drift_severity_critical():
    """Test that critical attribute changes (instance_type) get critical severity."""
    from tools.diff_tools import _classify_attribute_drift_severity
    
    attr_drift = {"modified_attributes": {"instance_type": {}}}
    severity = _classify_attribute_drift_severity(attr_drift, "aws_instance")
    
    assert severity == "critical"
