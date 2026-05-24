"""
conftest.py — pytest fixtures for Terraform Drift Detector.
"""

import json
import pytest
from unittest.mock import Mock, MagicMock
from langchain_core.documents import Document


@pytest.fixture
def mock_llm(mocker):
    """Mock OllamaLLM for testing (no real API calls)."""
    mock = Mock()
    mock.invoke.return_value = "Mocked LLM response"
    mocker.patch("common.llm_factory.get_llm", return_value=mock)
    return mock


@pytest.fixture
def mock_chat_llm(mocker):
    """Mock ChatOllama for testing (no real API calls)."""
    mock = Mock()
    
    # Mock the invoke method to return a properly structured response
    mock_message = Mock()
    mock_message.content = """**Policy Violation:**
policies/tags.yaml → production.required_tags[0]

**Impact:**
Instance not enrolled in automated backup schedule

**Compliance Frameworks Affected:**
- SOC2 Section 4.2.1
- HIPAA §164.308(a)(7)(ii)(A)

**Remediation:**
terraform apply -target=aws_instance.web-prod-01

**Verification Steps:**
1. Check tags with: aws ec2 describe-instances --instance-ids i-abc123
2. Verify backup enrollment in AWS Backup console"""
    
    mock.invoke.return_value = mock_message
    mocker.patch("common.llm_factory.get_chat_llm", return_value=mock)
    return mock


@pytest.fixture
def mock_embeddings(mocker):
    """Mock OllamaEmbeddings for testing (no real API calls)."""
    mock = Mock()
    mock.embed_documents.return_value = [[0.1] * 384]  # Mock embedding vector
    mock.embed_query.return_value = [0.1] * 384
    mocker.patch("common.llm_factory.get_embeddings", return_value=mock)
    return mock


@pytest.fixture
def sample_state_file_content():
    """Sample Terraform state file content."""
    return {
        "version": 4,
        "terraform_version": "1.5.0",
        "resources": [
            {
                "type": "aws_instance",
                "name": "web-prod-01",
                "instances": [
                    {
                        "attributes": {
                            "id": "i-0123456789abcdef0",
                            "instance_type": "t3.medium",
                            "ami": "ami-12345678",
                            "availability_zone": "us-east-1a",
                            "vpc_security_group_ids": ["sg-abc123"],
                            "tags": {
                                "Environment": "prod",
                                "Name": "web-prod-01",
                                "Owner": "team-platform"
                            }
                        },
                        "sensitive_attributes": []
                    }
                ]
            }
        ]
    }


@pytest.fixture
def sample_state_file_with_sensitive(tmp_path):
    """Create a temporary state file with sensitive attributes."""
    state_content = {
        "version": 4,
        "resources": [
            {
                "type": "aws_db_instance",
                "name": "db-prod-01",
                "instances": [
                    {
                        "attributes": {
                            "id": "db-prod-mysql-01",
                            "engine": "mysql",
                            "password": "supersecretpassword123",
                            "tags": {"Environment": "prod"}
                        },
                        "sensitive_attributes": [["password"]]
                    }
                ]
            }
        ]
    }
    
    state_file = tmp_path / "test.tfstate"
    state_file.write_text(json.dumps(state_content))
    return state_file


@pytest.fixture
def sample_state_file(tmp_path, sample_state_file_content):
    """Create a temporary Terraform state file."""
    state_file = tmp_path / "terraform.tfstate"
    state_file.write_text(json.dumps(sample_state_file_content))
    return state_file


@pytest.fixture
def mock_boto3_client(mocker):
    """Mock boto3 client for AWS API calls."""
    mock_client = MagicMock()
    
    # Mock EC2 describe_instances response
    mock_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0123456789abcdef0",
                        "InstanceType": "t3.medium",
                        "ImageId": "ami-12345678",
                        "Placement": {"AvailabilityZone": "us-east-1a"},
                        "SecurityGroups": [{"GroupId": "sg-abc123"}],
                        "Tags": [
                            {"Key": "Environment", "Value": "prod"},
                            {"Key": "Name", "Value": "web-prod-01"},
                            {"Key": "Owner", "Value": "team-platform"}
                        ]
                    }
                ]
            }
        ]
    }
    
    mocker.patch("boto3.client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_boto3_client_drift(mocker):
    """Mock boto3 client returning drifted resource state."""
    mock_client = MagicMock()
    
    # EC2 instance missing Environment tag (drift scenario)
    mock_client.describe_instances.return_value = {
        "Reservations": [
            {
                "Instances": [
                    {
                        "InstanceId": "i-0123456789abcdef0",
                        "InstanceType": "t3.medium",
                        "ImageId": "ami-12345678",
                        "Placement": {"AvailabilityZone": "us-east-1a"},
                        "SecurityGroups": [{"GroupId": "sg-abc123"}],
                        "Tags": [
                            # Missing "Environment" tag
                            {"Key": "Name", "Value": "web-prod-01-temp"},  # Modified tag
                            {"Key": "Owner", "Value": "team-platform"}
                        ]
                    }
                ]
            }
        ]
    }
    
    mocker.patch("boto3.client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_vector_store(mocker):
    """Mock Chroma vector store for testing."""
    mock = Mock()
    
    # Mock as_retriever method
    mock_retriever = Mock()
    mock_retriever.get_relevant_documents.return_value = [
        Document(
            page_content="""environments:
  production:
    required_tags:
      - name: Environment
        value: prod
        violations:
          missing: "Instance not enrolled in automated backup schedule"
        compliance_frameworks:
          - framework: SOC2
            section: "Section 4.2.1 - Data Retention"
          - framework: HIPAA
            section: "§164.308(a)(7)(ii)(A)" """,
            metadata={"source": "policies/tags.yaml"}
        )
    ]
    mock.as_retriever.return_value = mock_retriever
    
    mocker.patch("langchain_chroma.Chroma", return_value=mock)
    mocker.patch("langchain_chroma.Chroma.from_documents", return_value=mock)
    
    return mock


@pytest.fixture
def sample_drift_summary():
    """Sample drift summary from compare_resources tool."""
    return json.dumps({
        "total_drifted": 1,
        "drifted_resources": [
            {
                "resource_id": "i-0123456789abcdef0",
                "resource_type": "aws_instance",
                "resource_name": "web-prod-01",
                "drift_type": "tags_modified",
                "severity": "critical",
                "changes": {
                    "removed_tags": ["Environment"],
                    "modified_tags": {
                        "Name": {
                            "state_value": "web-prod-01",
                            "cloud_value": "web-prod-01-temp"
                        }
                    }
                }
            }
        ]
    })


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock AWS environment variables."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test_access_key")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test_secret_key")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")
