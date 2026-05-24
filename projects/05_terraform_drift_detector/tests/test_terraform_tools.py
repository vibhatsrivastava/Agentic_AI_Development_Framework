"""Tests for Terraform state parsing tools."""

import json
from tools.terraform_tools import parse_terraform_state


def test_parse_terraform_state_success(sample_state_file):
    """Test successful parsing of valid Terraform state file."""
    result_json = parse_terraform_state.invoke({"file_path": str(sample_state_file)})
    result = json.loads(result_json)
    
    assert "error" not in result
    assert result["total_resources"] == 1
    assert len(result["resources"]) == 1
    
    resource = result["resources"][0]
    assert resource["type"] == "aws_instance"
    assert resource["name"] == "web-prod-01"
    assert resource["id"] == "i-0123456789abcdef0"
    assert resource["tags"]["Environment"] == "prod"


def test_parse_terraform_state_redacts_sensitive(sample_state_file_with_sensitive):
    """Test that sensitive attributes are redacted."""
    result_json = parse_terraform_state.invoke({"file_path": str(sample_state_file_with_sensitive)})
    result = json.loads(result_json)
    
    assert "error" not in result
    resource = result["resources"][0]
    
    # Password should be redacted
    assert resource["attributes"].get("password") == "[REDACTED]"


def test_parse_terraform_state_invalid_extension():
    """Test rejection of non-.tfstate files."""
    result_json = parse_terraform_state.invoke({"file_path": "invalid.json"})
    result = json.loads(result_json)
    
    assert "error" in result
    assert ".tfstate" in result["error"]


def test_parse_terraform_state_file_not_found():
    """Test handling of missing state file."""
    result_json = parse_terraform_state.invoke({"file_path": "nonexistent.tfstate"})
    result = json.loads(result_json)
    
    assert "error" in result
    assert "not found" in result["error"].lower()


def test_parse_terraform_state_invalid_json(tmp_path):
    """Test handling of malformed JSON in state file."""
    invalid_state_file = tmp_path / "invalid.tfstate"
    invalid_state_file.write_text("{invalid json content")
    
    result_json = parse_terraform_state.invoke({"file_path": str(invalid_state_file)})
    result = json.loads(result_json)
    
    assert "error" in result
    assert "json" in result["error"].lower()


def test_parse_terraform_state_extracts_relevant_attributes(sample_state_file):
    """Test that only relevant attributes are extracted (avoid token overflow)."""
    result_json = parse_terraform_state.invoke({"file_path": str(sample_state_file)})
    result = json.loads(result_json)
    
    resource = result["resources"][0]
    attrs = resource["attributes"]
    
    # Should include relevant attributes
    assert "id" in attrs
    assert "instance_type" in attrs
    assert "tags" in attrs
    
    # Should not include irrelevant attributes (not explicitly extracted)
    # This is implicitly tested by the small size of attrs
    assert len(attrs) <= 10  # Keep attribute count reasonable
