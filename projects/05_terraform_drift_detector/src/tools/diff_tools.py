"""Resource comparison and drift detection tools."""

import json
from deepdiff import DeepDiff
from langchain_core.tools import tool
from common.utils import get_logger
from pydantic import BaseModel, model_validator

logger = get_logger(__name__)

def _compare_resources_impl(state_data: dict, cloud_data: dict) -> dict:
    """
    Compare Terraform state resources against cloud resources to detect drift.
    Args:
        state_data: dict from parse_terraform_state tool
        cloud_data: dict from fetch_cloud_resources tool
    Returns:
        dict with drift summary: {"total_drifted": int, "drifted_resources": [...]}
    """
    if "error" in state_data:
        return {"error": f"State parse error: {state_data['error']}"}
    if "error" in cloud_data:
        return {"error": f"Cloud fetch error: {cloud_data['error']}"}
    state_list = state_data.get("resources", [])
    cloud_list = cloud_data.get("resources", [])
    cloud_types = {r.get("type") for r in cloud_list if r.get("type")}
    explicit_cloud_type = cloud_data.get("resource_type")
    if explicit_cloud_type:
        cloud_types.add(explicit_cloud_type)

    drifted = []
    # Compare each state resource with its cloud counterpart
    for s_res in state_list:
        resource_id = s_res.get("id")
        state_type = s_res.get("type")
        if cloud_types and state_type not in cloud_types:
            logger.info(
                f"Skipping state resource {resource_id} of type {state_type} because cloud data only contains types {cloud_types}"
            )
            continue
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
        # Always use attributes['tags'] if present, else fallback to top-level 'tags'
        state_tags = s_res.get("attributes", {}).get("tags", s_res.get("tags", {}))
        cloud_tags = c_res.get("attributes", {}).get("tags", c_res.get("tags", {}))
        print(f"[DEBUG] Comparing tags for resource {resource_id}:\n  state_tags={state_tags}\n  cloud_tags={cloud_tags}")
        tag_drift = _compare_tags(state_tags, cloud_tags)
        print(f"[DEBUG] tag_drift for resource {resource_id}: {tag_drift}")
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
    return {
        "total_drifted": len(drifted),
        "drifted_resources": drifted
    }


class CompareResourcesArgs(BaseModel):
    state_resources: str | dict | list | None = None
    cloud_resources: str | dict | list | None = None
    payload: str | dict | None = None

    @model_validator(mode="before")
    def normalize_payload(cls, values):
        payload = values.get("payload")
        state_resources = values.get("state_resources")
        cloud_resources = values.get("cloud_resources")

        if payload is not None and isinstance(payload, dict):
            if "state_resources" in payload and "cloud_resources" in payload:
                if state_resources is None:
                    values["state_resources"] = payload.get("state_resources")
                if cloud_resources is None:
                    values["cloud_resources"] = payload.get("cloud_resources")
        return values


@tool(args_schema=CompareResourcesArgs)
def compare_resources(
    state_resources: str | dict | list | None = None,
    cloud_resources: str | dict | list | None = None,
    payload: str | dict | None = None,
) -> str:
    """
    Accepts state_resources and cloud_resources, each as a JSON string, dict, or list.
    """
    if payload is not None and isinstance(payload, dict):
        if state_resources is None and cloud_resources is None:
            state_resources = payload.get("state_resources")
            cloud_resources = payload.get("cloud_resources")

    if isinstance(state_resources, dict) and cloud_resources is None and "input" in state_resources:
        inner_payload = state_resources["input"]
        state_resources = inner_payload.get("state_resources")
        cloud_resources = inner_payload.get("cloud_resources")

    if isinstance(cloud_resources, dict) and state_resources is None and "input" in cloud_resources:
        inner_payload = cloud_resources["input"]
        state_resources = inner_payload.get("state_resources")
        cloud_resources = inner_payload.get("cloud_resources")

    # Strict input validation and debug print
    print(f"[DEBUG] compare_resources received state_resources type: {type(state_resources)}, cloud_resources type: {type(cloud_resources)}")
    if state_resources is None or cloud_resources is None:
        error_msg = "compare_resources requires both 'state_resources' and 'cloud_resources'"
        logger.error(error_msg)
        return json.dumps({"error": error_msg})

    # Debug print the raw input for payload validation
    try:
        import pprint
        print("[DEBUG] RAW compare_resources input (truncated):\n" + pprint.pformat({"state_resources": state_resources, "cloud_resources": cloud_resources})[:2000])
    except Exception:
        print("[DEBUG] RAW compare_resources input: <unprintable>")

    # Helper to filter resource fields
    def filter_resource_fields(resource):
        # Only keep id, tags, attributes, type, name
        allowed = {"id", "tags", "attributes", "type", "name"}
        return {k: v for k, v in resource.items() if k in allowed}

    # Filter state_resources and cloud_resources to minimal fields
    if isinstance(state_resources, list):
        state_resources = [filter_resource_fields(r) for r in state_resources]
    if isinstance(cloud_resources, list):
        cloud_resources = [filter_resource_fields(r) for r in cloud_resources]

    def ensure_resource_dict(val):
        # Accept dict with 'resources', or a list (wrap as dict), or JSON string
        if isinstance(val, dict):
            if 'resources' in val:
                return val
            if 'type' in val and 'id' in val:
                return {'resources': [val]}
            return val
        if isinstance(val, list):
            return {'resources': val}
        if isinstance(val, str):
            # Try to parse directly. If parsing fails, attempt lightweight sanitization
            try:
                parsed = json.loads(val)
                return ensure_resource_dict(parsed)
            except Exception as e:
                import re
                # Remove common truncation artifacts like ellipses and stray commas
                sanitized = re.sub(r"\.{3,}", "", val)
                sanitized = sanitized.replace(',}', '}').replace(',]', ']')
                try:
                    parsed = json.loads(sanitized)
                    logger.warning("[WARN] Input JSON contained truncation artifacts; used sanitized version for parsing.")
                    return ensure_resource_dict(parsed)
                except Exception as e2:
                    logger.error(f"[ERROR] Failed to parse input as JSON. Exception: {e}\nSanitized exception: {e2}\nRaw value: {val}")
                    return {'error': f'Invalid JSON input: {e}', 'raw': val}
        return {'resources': []}

    # Always wrap arrays as dicts with 'resources' key for both state and cloud
    if isinstance(state_resources, list):
        state_resources = {"resources": state_resources}
    if isinstance(cloud_resources, list):
        cloud_resources = {"resources": cloud_resources}

    state_dict = ensure_resource_dict(state_resources)
    cloud_dict = ensure_resource_dict(cloud_resources)
    result = _compare_resources_impl(state_dict, cloud_dict)
    json_result = json.dumps(result, indent=2)
    print("[DEBUG] FINAL compare_resources JSON output (to LLM):\n" + json_result)
    return json_result


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
