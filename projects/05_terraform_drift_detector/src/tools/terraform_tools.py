"""Terraform state parsing tools."""

import json
import re
from pathlib import Path
from langchain_core.tools import tool
from common.utils import get_logger

logger = get_logger(__name__)


@tool
def parse_terraform_state(file_path: str) -> str:
    """
    Parse Terraform state file and extract resource information.
    Redacts sensitive attributes before returning.
    
    Args:
        file_path: Path to .tfstate file
    
    Returns:
        JSON string with resource list: {"total_resources": int, "resources": [...]}
    """
    # Validate file path
    if not re.match(r"^[a-zA-Z0-9/_.-]+\.tfstate$", file_path):
        return json.dumps({"error": "Invalid state file path: must end with .tfstate"})
    
    file_path_obj = Path(file_path)
    if not file_path_obj.exists():
        return json.dumps({"error": f"State file not found: {file_path}"})
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON in state file: {str(e)}"})
    except Exception as e:
        return json.dumps({"error": f"Failed to read state file: {str(e)}"})
    
    # Extract resources
    resources = []
    for resource in state.get("resources", []):
        resource_type = resource.get("type", "unknown")
        resource_name = resource.get("name", "unknown")
        
        for instance in resource.get("instances", []):
            attributes = instance.get("attributes", {})
            
            # Redact sensitive attributes
            sensitive_attrs = instance.get("sensitive_attributes", [])
            redacted_attrs = _redact_sensitive_attributes(attributes, sensitive_attrs)
            
            # Extract only relevant attributes to avoid token overflow
            relevant_attrs = _extract_relevant_attributes(redacted_attrs, resource_type)
            
            resources.append({
                "type": resource_type,
                "name": resource_name,
                "id": relevant_attrs.get("id", "unknown"),
                "tags": relevant_attrs.get("tags", {}),
                "attributes": relevant_attrs,
            })
    
    logger.info(f"Parsed {len(resources)} resources from state file")
    return json.dumps({
        "total_resources": len(resources),
        "resources": resources
    }, indent=2)


def _redact_sensitive_attributes(attributes: dict, sensitive_paths: list) -> dict:
    """
    Redact sensitive attributes in-place.
    
    Args:
        attributes: Resource attributes dictionary
        sensitive_paths: List of paths to sensitive attributes (nested lists)
    
    Returns:
        Attributes dict with sensitive values replaced with [REDACTED]
    """
    import logging
    redacted = attributes.copy()

    for path in sensitive_paths:
        if not path or not isinstance(path, list):
            continue

        # Only handle paths where all elements are strings
        if not all(isinstance(k, str) for k in path):
            logger.warning(f"Skipping sensitive path with non-string keys: {path}")
            continue

        current = redacted
        for key in path[:-1]:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                break

        # Redact the final key
        if isinstance(current, dict) and path[-1] in current:
            current[path[-1]] = "[REDACTED]"

    return redacted


def _extract_relevant_attributes(attributes: dict, resource_type: str) -> dict:
    """
    Extract only relevant attributes for drift detection to avoid token overflow.
    
    Args:
        attributes: Full resource attributes
        resource_type: Terraform resource type
    
    Returns:
        Dictionary with only relevant attributes
    """
    # Common attributes for all resources
    relevant = {
        "id": attributes.get("id"),
        "tags": attributes.get("tags", {}),
    }
    
    # Resource-specific attributes
    if resource_type == "aws_instance":
        relevant.update({
            "instance_type": attributes.get("instance_type"),
            "ami": attributes.get("ami"),
            "availability_zone": attributes.get("availability_zone"),
            "vpc_security_group_ids": attributes.get("vpc_security_group_ids", []),
        })
    elif resource_type == "aws_db_instance":
        password = attributes.get("password")
        relevant.update({
            "engine": attributes.get("engine"),
            "engine_version": attributes.get("engine_version"),
            "instance_class": attributes.get("instance_class"),
            "allocated_storage": attributes.get("allocated_storage"),
            # Never expose plaintext password values in parsed output
            "password": "[REDACTED]" if password is not None else None,
        })
    elif resource_type == "aws_security_group":
        relevant.update({
            "name": attributes.get("name"),
            "description": attributes.get("description"),
            "vpc_id": attributes.get("vpc_id"),
            "ingress": attributes.get("ingress", []),
            "egress": attributes.get("egress", []),
        })
    elif resource_type == "aws_s3_bucket":
        relevant.update({
            "bucket": attributes.get("bucket"),
            "region": attributes.get("region"),
            "versioning": attributes.get("versioning"),
        })
    
    return relevant
