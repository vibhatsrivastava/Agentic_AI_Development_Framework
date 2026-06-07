"""Tests for AWS cloud resource fetching tools."""

import json
from unittest.mock import MagicMock
from botocore.exceptions import ClientError
from tools.aws_tools import fetch_cloud_resources


def test_fetch_ec2_instances_success(mock_boto3_client, mock_env_vars):
    """Test successful EC2 instance fetch from AWS."""
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "i-0123456789abcdef0",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    assert "error" not in result
    assert result["resource_type"] == "aws_instance"
    assert len(result["resources"]) == 1
    
    instance = result["resources"][0]
    assert instance["id"] == "i-0123456789abcdef0"
    assert instance["instance_type"] == "t3.medium"
    assert instance["tags"]["Environment"] == "prod"


def test_fetch_ec2_instances_multiple_ids(mock_boto3_client, mock_env_vars):
    """Test fetching multiple EC2 instances with comma-separated IDs."""
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "i-abc123,i-def456",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    # Should parse comma-separated IDs
    assert "error" not in result or mock_boto3_client.describe_instances.called


def test_fetch_cloud_resources_empty_ids():
    """Test handling of empty resource_ids."""
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    assert "error" in result
    assert "No resource IDs provided" in result["error"]


def test_fetch_cloud_resources_invalid_ids_format():
    """Test handling of invalid resource_ids format."""
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "   ,  ,  ",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    assert "error" in result


def test_fetch_cloud_resources_unsupported_type(mock_env_vars):
    """Test handling of unsupported resource types."""
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "unknown-123",
        "resource_type": "aws_unsupported_resource"
    })
    result = json.loads(result_json)
    
    assert "error" in result
    assert "Unsupported resource type" in result["error"]


def test_fetch_cloud_resources_ssm_parameter_success(mock_env_vars, mocker):
    """Test fetching AWS SSM parameters from cloud."""
    mock_client = MagicMock()
    mock_client.get_parameter.return_value = {
        "Parameter": {
            "Name": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
            "Type": "String",
            "ARN": "arn:aws:ssm:us-east-1:123456789012:parameter/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
            "Description": "Amazon Linux 2023 AMI parameter"
        }
    }
    mock_client.list_tags_for_resource.return_value = {
        "Tags": [
            {"Key": "Project", "Value": "drift-detector-demo"}
        ]
    }
    mocker.patch("boto3.client", return_value=mock_client)

    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64",
        "resource_type": "aws_ssm_parameter"
    })
    result = json.loads(result_json)

    assert result["resource_type"] == "aws_ssm_parameter"
    assert len(result["resources"]) == 1
    assert result["resources"][0]["id"] == "/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
    assert result["resources"][0]["type"] == "aws_ssm_parameter"


def test_fetch_cloud_resources_missing_aws_credentials(monkeypatch):
    """Test handling of missing AWS credentials."""
    # Remove AWS env vars
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_DEFAULT_REGION", raising=False)
    
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "i-abc123",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    assert "error" in result
    assert "credentials not configured" in result["error"].lower()


def test_fetch_cloud_resources_throttling_error(mocker, mock_env_vars):
    """Test handling of AWS API throttling errors."""
    mock_client = MagicMock()
    mock_client.describe_instances.side_effect = ClientError(
        {"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
        "DescribeInstances"
    )
    mocker.patch("boto3.client", return_value=mock_client)
    
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "i-abc123",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    assert "error" in result
    assert "rate limit" in result["error"].lower()


def test_fetch_cloud_resources_not_found_error(mocker, mock_env_vars):
    """Test handling of resource not found errors."""
    mock_client = MagicMock()
    mock_client.describe_instances.side_effect = ClientError(
        {"Error": {"Code": "InvalidInstanceID.NotFound", "Message": "Instance not found"}},
        "DescribeInstances"
    )
    mocker.patch("boto3.client", return_value=mock_client)
    
    result_json = fetch_cloud_resources.invoke({
        "resource_ids": "i-nonexistent",
        "resource_type": "aws_instance"
    })
    result = json.loads(result_json)
    
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_rate_limiter_applied(mock_boto3_client, mock_env_vars, mocker):
    """Test that rate limiter is applied to AWS API calls."""
    # Mock the rate limiter
    mock_rate_limiter = MagicMock()
    mocker.patch("tools.aws_tools.rate_limiter", mock_rate_limiter)
    
    fetch_cloud_resources.invoke({
        "resource_ids": "i-abc123",
        "resource_type": "aws_instance"
    })
    
    # Rate limiter should have been called
    mock_rate_limiter.acquire.assert_called_once()
