"""Resource comparison and drift detection tools."""

import json
from deepdiff import DeepDiff
from langchain_core.tools import tool
from common.utils import get_logger

logger = get_logger(__name__)


@tool
def compare_resources(state_resources: str, cloud_resources: str) -> str:
    """
    Compare Terraform state resources against cloud resources to detect drift.
    
    Args:
        state_resources: JSON string from parse_terraform_state tool
        cloud_resources: JSON string from fetch_cloud_resources tool
    
    Returns:
        JSON string with drift summary: {"total_drifted": int, "drifted_resources": [...]}
    """
    # Parse input JSON strings
    try:
        state_data = json.loads(state_resources)
        cloud_data = json.loads(cloud_resources)
    except json.JSONDecodeError as e:
        return json.dumps({"error": f"Invalid JSON input: {str(e)}"})
    
    # Handle error responses from previous tools
    if "error" in state_data:
        return json.dumps({"error": f"State parse error: {state_data['error']}"})
    if "error" in cloud_data:
        return json.dumps({"error": f"Cloud fetch error: {cloud_data['error']}"})
    
    state_list = state_data.get("resources", [])
    cloud_list = cloud_data.get("resources", [])
    
    if not state_list:
        return json.dumps({"error": "No resources in state file"})
    if not cloud_list:
        return json.dumps({"error": "No resources fetched from cloud"})
    
    # Compare each state resource with its cloud counterpart
    drifted = []
    
    for s_res in state_list:
        resource_id = s_res.get("id")
        if not resource_id or resource_id == "unknown":
            continue
        
        # Find matching cloud resource by ID
        c_res = next((r for r in cloud_list if r.get("id") == resource_id), None)
        
        if not c_res:
            # Resource exists in state but not in cloud (deleted outside Terraform)
            drifted.append({
                "resource_id": resource_id,
                "resource_type": s_res.get("type"),
                "resource_name": s_res.get("name"),
                "drift_type": "resource_deleted",
                "severity": "critical",
                "changes": {
                    "details": "Resource deleted outside Terraform"
                },
            })
            continue
        
        # Compare tags
        tag_drift = _compare_tags(s_res.get("tags", {}), c_res.get("tags", {}))
        if tag_drift:
            drifted.append({
                "resource_id": resource_id,
                "resource_type": s_res.get("type"),
                "resource_name": s_res.get("name"),
                "drift_type": "tags_modified",
                "severity": _classify_tag_drift_severity(tag_drift),
                "changes": tag_drift,
            })
        
        # Compare attributes (excluding tags and timestamps)
        attr_drift = _compare_attributes(
            s_res.get("attributes", {}),
            c_res.get("attributes", {}),
            s_res.get("type")
        )
        if attr_drift:
            drifted.append({
                "resource_id": resource_id,
                "resource_type": s_res.get("type"),
                "resource_name": s_res.get("name"),
                "drift_type": "attributes_changed",
                "severity": _classify_attribute_drift_severity(attr_drift, s_res.get("type")),
                "changes": attr_drift,
            })
    
    # Check for resources in cloud but not in state (created outside Terraform)
    state_ids = {r.get("id") for r in state_list if r.get("id")}
    for c_res in cloud_list:
        if c_res.get("id") not in state_ids:
            drifted.append({
                "resource_id": c_res.get("id"),
                "resource_type": cloud_data.get("resource_type"),
                "resource_name": "unknown",
                "drift_type": "resource_created",
                "severity": "medium",
                "changes": {
                    "details": "Resource created outside Terraform"
                },
            })
    
    logger.info(f"Found {len(drifted)} drifted resources")
    return json.dumps({
        "total_drifted": len(drifted),
        "drifted_resources": drifted
    }, indent=2)


def _compare_tags(state_tags: dict, cloud_tags: dict) -> dict:
    """
    Compare tags between state and cloud.
    
    Returns:
        Dictionary with removed_tags, added_tags, modified_tags (empty dict if no drift)
    """
    diff = DeepDiff(state_tags, cloud_tags, ignore_order=True)
    
    if not diff:
        return {}
    
    result = {}
    
    # Tags removed in cloud
    if "dictionary_item_removed" in diff:
        result["removed_tags"] = [key.replace("root['", "").replace("']", "") 
                                  for key in diff["dictionary_item_removed"]]
    
    # Tags added in cloud
    if "dictionary_item_added" in diff:
        result["added_tags"] = [key.replace("root['", "").replace("']", "") 
                               for key in diff["dictionary_item_added"]]
    
    # Tags with modified values
    if "values_changed" in diff:
        result["modified_tags"] = {
            key.replace("root['", "").replace("']", ""): {
                "state_value": change["old_value"],
                "cloud_value": change["new_value"]
            }
            for key, change in diff["values_changed"].items()
        }
    
    return result


def _compare_attributes(state_attrs: dict, cloud_attrs: dict, resource_type: str) -> dict:
    """
    Compare resource attributes (excluding tags).
    
    Returns:
        Dictionary with changed attributes (empty dict if no drift)
    """
    # Exclude tags and timestamp fields
    exclude_keys = {"tags", "id", "arn", "created_time", "last_modified", "last_updated"}
    
    state_filtered = {k: v for k, v in state_attrs.items() if k not in exclude_keys}
    cloud_filtered = {k: v for k, v in cloud_attrs.items() if k not in exclude_keys}
    
    diff = DeepDiff(state_filtered, cloud_filtered, ignore_order=True)
    
    if not diff:
        return {}
    
    result = {}
    
    # Attribute values changed
    if "values_changed" in diff:
        result["modified_attributes"] = {
            key.replace("root['", "").replace("']", ""): {
                "state_value": change["old_value"],
                "cloud_value": change["new_value"]
            }
            for key, change in diff["values_changed"].items()
        }
    
    # Attributes removed
    if "dictionary_item_removed" in diff:
        result["removed_attributes"] = [key.replace("root['", "").replace("']", "") 
                                       for key in diff["dictionary_item_removed"]]
    
    # Attributes added
    if "dictionary_item_added" in diff:
        result["added_attributes"] = [key.replace("root['", "").replace("']", "") 
                                     for key in diff["dictionary_item_added"]]
    
    return result


def _classify_tag_drift_severity(tag_drift: dict) -> str:
    """
    Classify tag drift severity based on which tags changed.
    
    Args:
        tag_drift: Dictionary with removed_tags, added_tags, modified_tags
    
    Returns:
        Severity level: critical, high, medium, low
    """
    critical_tags = {"Environment", "Backup", "Compliance", "DataClassification"}
    high_tags = {"Owner", "CostCenter", "Name"}
    
    removed = set(tag_drift.get("removed_tags", []))
    modified = set(tag_drift.get("modified_tags", {}).keys())
    
    if removed & critical_tags or modified & critical_tags:
        return "critical"
    if removed & high_tags or modified & high_tags:
        return "high"
    if removed or modified:
        return "medium"
    
    return "low"


def _classify_attribute_drift_severity(attr_drift: dict, resource_type: str) -> str:
    """
    Classify attribute drift severity based on resource type and changed attributes.
    
    Args:
        attr_drift: Dictionary with modified_attributes, removed_attributes, added_attributes
        resource_type: Terraform resource type
    
    Returns:
        Severity level: critical, high, medium, low
    """
    modified_attrs = set(attr_drift.get("modified_attributes", {}).keys())
    
    # Critical attributes per resource type
    critical_attrs_map = {
        "aws_instance": {"instance_type", "ami"},
        "aws_db_instance": {"engine", "instance_class", "allocated_storage"},
        "aws_security_group": {"ingress", "egress"},
        "aws_s3_bucket": {"versioning", "encryption"},
    }
    
    critical_attrs = critical_attrs_map.get(resource_type, set())
    
    if modified_attrs & critical_attrs:
        return "critical"
    if modified_attrs:
        return "medium"
    
    return "low"
