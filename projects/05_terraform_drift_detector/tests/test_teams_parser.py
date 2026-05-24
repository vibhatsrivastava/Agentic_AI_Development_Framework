"""Tests for teams.yaml parser and assignee resolution."""

import pytest
import tempfile
import os
from pathlib import Path
from src.utils.teams_parser import (
    parse_teams_config,
    get_resource_assignee,
    validate_teams_config,
)


@pytest.fixture
def sample_teams_config():
    """Sample teams.yaml configuration for testing."""
    return {
        "resource_ownership": {
            "ec2": {
                "default_owner": "@infrastructure-team",
                "patterns": [
                    {"pattern": "web-.*", "owner": "@web-team"},
                    {"pattern": "api-.*", "owner": "@backend-team"},
                    {"pattern": ".*-prod-.*", "owner": "@production-team"},
                ],
            },
            "rds": {
                "default_owner": "@database-team",
                "patterns": [
                    {"pattern": "postgres-.*", "owner": "@postgres-admin"},
                    {"pattern": "mysql-.*", "owner": "@mysql-admin"},
                ],
            },
            "s3": {
                "default_owner": "@storage-team",
                "patterns": [],
            },
        }
    }


@pytest.fixture
def teams_yaml_file(sample_teams_config):
    """Create a temporary teams.yaml file for testing."""
    import yaml
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(sample_teams_config, f)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)


def test_parse_teams_config(teams_yaml_file):
    """Test parsing teams.yaml configuration."""
    config = parse_teams_config(teams_yaml_file)
    
    assert "resource_ownership" in config
    assert "ec2" in config["resource_ownership"]
    assert "rds" in config["resource_ownership"]
    assert "s3" in config["resource_ownership"]


def test_parse_teams_config_file_not_found():
    """Test parsing non-existent teams.yaml file."""
    with pytest.raises(FileNotFoundError):
        parse_teams_config("/nonexistent/path/teams.yaml")


def test_get_resource_assignee_pattern_match(sample_teams_config, monkeypatch):
    """Test assignee resolution with pattern matching."""
    # Test EC2 web server pattern
    assignee = get_resource_assignee("aws_instance", "web-prod-01", sample_teams_config)
    assert assignee == "@web-team"
    
    # Test EC2 API server pattern
    assignee = get_resource_assignee("aws_instance", "api-staging-02", sample_teams_config)
    assert assignee == "@backend-team"
    
    # Test RDS postgres pattern
    assignee = get_resource_assignee("aws_db_instance", "postgres-main", sample_teams_config)
    assert assignee == "@postgres-admin"


def test_get_resource_assignee_prod_pattern_priority(sample_teams_config):
    """Test pattern matching priority (first match wins)."""
    # web-prod-01 matches both "web-.*" and ".*-prod-.*"
    # Should return first match: @web-team
    assignee = get_resource_assignee("aws_instance", "web-prod-01", sample_teams_config)
    assert assignee == "@web-team"


def test_get_resource_assignee_default_owner(sample_teams_config):
    """Test fallback to default owner when no pattern matches."""
    # EC2 instance with no matching pattern
    assignee = get_resource_assignee("aws_instance", "random-server-99", sample_teams_config)
    assert assignee == "@infrastructure-team"
    
    # S3 bucket (no patterns defined, should use default)
    assignee = get_resource_assignee("aws_s3_bucket", "my-data-bucket", sample_teams_config)
    assert assignee == "@storage-team"


def test_get_resource_assignee_env_fallback(sample_teams_config, monkeypatch):
    """Test fallback to GITHUB_ISSUE_ASSIGNEE environment variable."""
    monkeypatch.setenv("GITHUB_ISSUE_ASSIGNEE", "@fallback-team")
    
    # Security group (not in config, should use env var)
    assignee = get_resource_assignee("aws_security_group", "sg-12345", sample_teams_config)
    assert assignee == "@fallback-team"


def test_get_resource_assignee_no_fallback(sample_teams_config):
    """Test when no assignee can be determined (returns None)."""
    # Security group with no env var set
    assignee = get_resource_assignee("aws_security_group", "sg-67890", sample_teams_config)
    assert assignee is None


def test_get_resource_assignee_resource_type_mapping(sample_teams_config):
    """Test resource type to config key mapping."""
    # aws_instance → ec2
    assignee = get_resource_assignee("aws_instance", "web-server", sample_teams_config)
    assert assignee == "@web-team"
    
    # aws_db_instance → rds
    assignee = get_resource_assignee("aws_db_instance", "postgres-db", sample_teams_config)
    assert assignee == "@postgres-admin"
    
    # aws_s3_bucket → s3
    assignee = get_resource_assignee("aws_s3_bucket", "logs-bucket", sample_teams_config)
    assert assignee == "@storage-team"


def test_validate_teams_config_valid(sample_teams_config):
    """Test validation of valid teams.yaml configuration."""
    # Should not raise any exceptions
    try:
        validate_teams_config(sample_teams_config)
    except Exception as e:
        pytest.fail(f"Validation failed for valid config: {e}")


def test_validate_teams_config_missing_key():
    """Test validation with missing required key."""
    invalid_config = {
        "resource_ownership": {
            "ec2": {
                # Missing default_owner
                "patterns": [],
            }
        }
    }
    
    with pytest.raises(ValueError, match="default_owner"):
        validate_teams_config(invalid_config)


def test_validate_teams_config_invalid_pattern():
    """Test validation with invalid pattern structure."""
    invalid_config = {
        "resource_ownership": {
            "ec2": {
                "default_owner": "@team",
                "patterns": [
                    {"pattern": "web-.*"}  # Missing owner
                ],
            }
        }
    }
    
    with pytest.raises(ValueError, match="owner"):
        validate_teams_config(invalid_config)


def test_get_resource_assignee_empty_config():
    """Test with empty configuration."""
    empty_config = {"resource_ownership": {}}
    
    assignee = get_resource_assignee("aws_instance", "test", empty_config)
    assert assignee is None


def test_get_resource_assignee_case_insensitive_pattern(sample_teams_config):
    """Test that pattern matching is case-sensitive (default regex behavior)."""
    # "WEB-server" should NOT match "web-.*" pattern (case-sensitive)
    assignee = get_resource_assignee("aws_instance", "WEB-server", sample_teams_config)
    assert assignee == "@infrastructure-team"  # Falls back to default
    
    # "web-server" should match "web-.*" pattern
    assignee = get_resource_assignee("aws_instance", "web-server", sample_teams_config)
    assert assignee == "@web-team"


def test_parse_teams_config_default_path(monkeypatch, teams_yaml_file):
    """Test parsing with default path resolution."""
    # Create a mock project structure
    project_root = Path(teams_yaml_file).parent
    policies_dir = project_root / "policies"
    policies_dir.mkdir(exist_ok=True)
    
    # Copy teams.yaml to expected location
    import shutil
    expected_path = policies_dir / "teams.yaml"
    shutil.copy(teams_yaml_file, expected_path)
    
    try:
        # Change to project root directory
        original_cwd = os.getcwd()
        os.chdir(project_root)
        
        # Parse without explicit path (should find policies/teams.yaml)
        config = parse_teams_config()
        
        assert "resource_ownership" in config
    finally:
        os.chdir(original_cwd)
        shutil.rmtree(policies_dir)
