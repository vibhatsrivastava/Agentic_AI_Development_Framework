"""Clean tests for resource comparison and drift detection tools."""

import json
import pytest
from tools.diff_tools import compare_resources, compare_resources_raw


# -------------------------
# Helpers
# -------------------------

def invoke(payload: dict):
    """Standardized tool invocation."""
    return json.loads(compare_resources.invoke(payload))


# -------------------------
# Core Drift Tests
# -------------------------

def test_no_drift_when_resources_match():
    payload = {
        "state_resources": {
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web-prod-01",
                    "id": "i-abc123",
                    "tags": {"Environment": "prod", "Name": "web-prod-01"},
                    "attributes": {"instance_type": "t3.medium"},
                }
            ]
        },
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [
                {
                    "id": "i-abc123",
                    "tags": {"Environment": "prod", "Name": "web-prod-01"},
                    "attributes": {"instance_type": "t3.medium"},
                }
            ],
        },
    }

    result = invoke(payload)

    assert result["total_drifted"] == 0
    assert result["drifted_resources"] == []


def test_tags_modified_detection():
    payload = {
        "state_resources": {
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web-prod-01",
                    "id": "i-abc123",
                    "tags": {"Environment": "prod", "Name": "web-prod-01"},
                    "attributes": {},
                }
            ]
        },
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [
                {
                    "id": "i-abc123",
                    "tags": {"Name": "web-prod-01-temp"},
                    "attributes": {},
                }
            ],
        },
    }

    result = invoke(payload)

    drift = result["drifted_resources"][0]

    assert result["total_drifted"] == 1
    assert drift["drift_type"] == "tags_modified"
    assert "Environment" in drift["changes"]["removed_tags"]
    assert "Name" in drift["changes"]["modified_tags"]


def test_attribute_changes_detected():
    payload = {
        "state_resources": {
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web-prod-01",
                    "id": "i-abc123",
                    "tags": {},
                    "attributes": {"instance_type": "t3.medium"},
                }
            ]
        },
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [
                {
                    "id": "i-abc123",
                    "tags": {},
                    "attributes": {"instance_type": "t3.large"},
                }
            ],
        },
    }

    result = invoke(payload)

    drift = result["drifted_resources"][0]

    assert result["total_drifted"] == 1
    assert drift["drift_type"] == "attributes_changed"
    assert "instance_type" in drift["changes"]["modified_attributes"]


def test_resource_deleted_detected():
    payload = {
        "state_resources": {
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web-prod-01",
                    "id": "i-abc123",
                    "tags": {},
                    "attributes": {},
                }
            ]
        },
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [],
        },
    }

    result = invoke(payload)

    drift = result["drifted_resources"][0]

    assert result["total_drifted"] == 1
    assert drift["drift_type"] == "resource_deleted"
    assert drift["severity"] == "critical"


def test_resource_created_detected():
    payload = {
        "state_resources": {"resources": []},
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [
                {
                    "id": "i-xyz999",
                    "tags": {},
                    "attributes": {},
                }
            ],
        },
    }

    result = invoke(payload)

    drift = result["drifted_resources"][0]

    assert result["total_drifted"] == 1
    assert drift["drift_type"] == "resource_created"
    assert drift["resource_id"] == "i-xyz999"


# -------------------------
# Error Handling
# -------------------------

def test_invalid_json_input_returns_error():
    payload = {
        "state_resources": "{invalid json",
        "cloud_resources": "{}",
    }

    result = invoke(payload)

    assert "error" in result


def test_error_in_state_payload_propagates():
    payload = {
        "state_resources": {"error": "State parse failed"},
        "cloud_resources": {"resources": []},
    }

    result = invoke(payload)

    assert "error" in result


# -------------------------
# Wrapper / Agent Input Formats
# -------------------------

def test_nested_payload_wrapper_supported():
    payload = {
        "payload": {
            "state_resources": {
                "resources": [
                    {
                        "type": "aws_instance",
                        "name": "web-prod-01",
                        "id": "i-abc123",
                        "tags": {"Environment": "prod"},
                        "attributes": {"instance_type": "t3.medium"},
                    }
                ]
            },
            "cloud_resources": {
                "resource_type": "aws_instance",
                "resources": [
                    {
                        "id": "i-abc123",
                        "tags": {"Environment": "prod"},
                        "attributes": {"instance_type": "t3.medium"},
                    }
                ],
            },
        }
    }

    result = invoke(payload)

    assert result["total_drifted"] == 0


def test_native_dict_inputs_supported():
    payload = {
        "state_resources": {
            "resources": [
                {
                    "type": "aws_instance",
                    "name": "web-prod-01",
                    "id": "i-abc123",
                    "tags": {"Environment": "prod"},
                    "attributes": {"instance_type": "t3.medium"},
                }
            ]
        },
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [
                {
                    "id": "i-abc123",
                    "tags": {"Environment": "prod"},
                    "attributes": {"instance_type": "t3.medium"},
                }
            ],
        },
    }

    result = invoke(payload)

    assert result["total_drifted"] == 0


# -------------------------
# Raw Parser Recovery
# -------------------------

def test_raw_tool_recovers_nested_json_strings():
    inner_cloud = {
        "resource_type": "aws_instance",
        "resources": [
            {
                "id": "i-abc123",
                "type": "aws_instance",
                "name": "web-prod-01",
                "tags": {"Environment": "prod"},
                "attributes": {"instance_type": "t3.medium"},
            }
        ],
    }

    inner_state = {
        "resources": [
            {
                "type": "aws_instance",
                "name": "web-prod-01",
                "id": "i-abc123",
                "tags": {"Environment": "prod"},
                "attributes": {"instance_type": "t3.medium"},
            }
        ],
    }

    raw_payload = json.dumps(
        {
            "cloud_resources": json.dumps(inner_cloud),
            "state_resources": json.dumps(inner_state),
        }
    )

    result = json.loads(compare_resources_raw.func(raw=raw_payload))

    assert result["total_drifted"] == 0
    assert result["drifted_resources"] == []


# -------------------------
# Mixed Resource Filtering
# -------------------------

def test_unsupported_state_resources_are_ignored():
    payload = {
        "state_resources": {
            "resources": [
                {
                    "type": "aws_ssm_parameter",
                    "name": "amazon_linux_2023_ami",
                    "id": "/aws/service/ami-amazon-linux-latest/al2023",
                    "tags": {},
                    "attributes": {},
                },
                {
                    "type": "aws_instance",
                    "name": "drift_test",
                    "id": "i-abc123",
                    "tags": {"Environment": "prod"},
                    "attributes": {"instance_type": "t3.medium"},
                },
            ]
        },
        "cloud_resources": {
            "resource_type": "aws_instance",
            "resources": [
                {
                    "id": "i-abc123",
                    "tags": {"Environment": "prod"},
                    "attributes": {"instance_type": "t3.medium"},
                }
            ],
        },
    }

    result = invoke(payload)

    assert result["total_drifted"] == 0


# -------------------------
# Classification Logic Tests
# -------------------------

def test_tag_severity_classification():
    from tools.diff_tools import _classify_tag_drift_severity

    assert (
        _classify_tag_drift_severity({"removed_tags": ["Environment", "Backup"]})
        == "critical"
    )

    assert (
        _classify_tag_drift_severity({"removed_tags": ["Owner"]})
        == "high"
    )


def test_attribute_severity_classification():
    from tools.diff_tools import _classify_attribute_drift_severity

    severity = _classify_attribute_drift_severity(
        {"modified_attributes": {"instance_type": {}}},
        "aws_instance",
    )

    assert severity == "critical"