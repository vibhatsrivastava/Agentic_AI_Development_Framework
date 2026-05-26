"""Resource comparison and drift detection tools."""

import json
import re
import ast
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
        # Support being called with a raw JSON string (truncated or not).
        try:
            # If values is a plain string, attempt to sanitize/parse it into a dict
            if isinstance(values, str):
                raw = values
                # small sanitizer similar to ensure_resource_dict
                def try_parse(s: str):
                    try:
                        return json.loads(s)
                    except Exception:
                        pass
                    try:
                        return ast.literal_eval(s)
                    except Exception:
                        pass
                    return None

                parsed = try_parse(raw)
                if parsed is None:
                    cleaned = re.sub(r'\.{2,}', '', raw)
                    cleaned = re.sub(r',\s*(?=[}\]])', '', cleaned)
                    parsed = try_parse(cleaned)
                if isinstance(parsed, dict):
                    values = parsed
                else:
                    # Return as-is so validation can proceed and function can handle errors
                    return {"payload": values}

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
        except Exception:
            # If anything goes wrong, return values unchanged to allow downstream handling
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

    # Debug: show incoming raw payload/state strings when present
    try:
        if isinstance(payload, str):
            print(f"[DEBUG] incoming payload string (len={len(payload)}): {payload[:500]}")
        if isinstance(state_resources, str):
            print(f"[DEBUG] incoming state_resources string (len={len(state_resources)}): {state_resources[:500]}")
    except Exception:
        pass

    # If payload or state_resources are raw strings that may contain both
    # `state_resources` and `cloud_resources`, try a best-effort parse before
    # enforcing that both are present. This helps when LLM/tool outputs are
    # truncated or embedded as a raw JSON-like string.
    def try_parse_payload_string(s: str):
        def _try(s2: str):
            try:
                return json.loads(s2)
            except Exception:
                pass
            try:
                return ast.literal_eval(s2)
            except Exception:
                pass
            return None

        if not isinstance(s, str):
            return None
        parsed = _try(s)
        if parsed is not None:
            return parsed
        cleaned = re.sub(r'\.{2,}', '', s)
        cleaned = re.sub(r',\s*(?=[}\]])', '', cleaned)
        parsed = _try(cleaned)
        if parsed is not None:
            return parsed
        m_obj = re.search(r"(\{.*\})", cleaned, flags=re.S)
        if m_obj:
            snippet = m_obj.group(1)
            parsed = _try(snippet)
            if parsed is not None:
                return parsed
        m_arr = re.search(r"(\[.*\])", cleaned, flags=re.S)
        if m_arr:
            snippet = m_arr.group(1)
            parsed = _try(snippet)
            if parsed is not None:
                return parsed
        return None

    def extract_json_field(s: str, field: str):
        # Find the field name in the string and attempt to extract the following
        # JSON object/array by scanning for matching braces. Returns parsed value
        # or None.
        if not isinstance(s, str):
            return None
        pat = re.compile(r'"' + re.escape(field) + r'"\s*:\s*')
        m = pat.search(s)
        if not m:
            return None
        idx = m.end()
        # Skip whitespace
        while idx < len(s) and s[idx].isspace():
            idx += 1
        if idx >= len(s):
            return None
        # Determine whether next token is object or array
        if s[idx] not in ('{', '['):
            return None
        open_ch = s[idx]
        close_ch = '}' if open_ch == '{' else ']'
        depth = 0
        end_idx = idx
        for i in range(idx, len(s)):
            ch = s[i]
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        snippet = s[idx:end_idx]
        if not snippet:
            return None
        try:
            return json.loads(snippet)
        except Exception:
            try:
                return ast.literal_eval(snippet)
            except Exception:
                # Fallback: attempt cleaning and parse
                cleaned = re.sub(r'\.{2,}', '', snippet)
                cleaned = re.sub(r',\s*(?=[}\]])', '', cleaned)
                try:
                    return json.loads(cleaned)
                except Exception:
                    try:
                        return ast.literal_eval(cleaned)
                    except Exception:
                        return None

    # Try parsing payload string
    if payload is not None and isinstance(payload, str):
        # Try parsing the whole payload first
        parsed_payload = try_parse_payload_string(payload)
        if isinstance(parsed_payload, dict):
            if state_resources is None and "state_resources" in parsed_payload:
                state_resources = parsed_payload.get("state_resources")
            if cloud_resources is None and "cloud_resources" in parsed_payload:
                cloud_resources = parsed_payload.get("cloud_resources")
        # If that failed, try extracting individual fields heuristically
        if state_resources is None:
            ext = extract_json_field(payload, "state_resources")
            if ext is not None:
                state_resources = ext
        if cloud_resources is None:
            ext = extract_json_field(payload, "cloud_resources")
            if ext is not None:
                cloud_resources = ext

    # Also try parsing when state_resources itself is a raw string that may
    # embed both fields
    if state_resources is not None and isinstance(state_resources, str) and cloud_resources is None:
        parsed_state = try_parse_payload_string(state_resources)
        if isinstance(parsed_state, dict):
            if "state_resources" in parsed_state and "cloud_resources" in parsed_state:
                state_resources = parsed_state.get("state_resources")
                cloud_resources = parsed_state.get("cloud_resources")
            else:
                # If parsed_state contains only one of the fields, pick it up
                if "cloud_resources" in parsed_state and cloud_resources is None:
                    cloud_resources = parsed_state.get("cloud_resources")
                if "state_resources" in parsed_state:
                    state_resources = parsed_state.get("state_resources")
        # Heuristic extraction of embedded JSON fields
        if cloud_resources is None:
            ext = extract_json_field(state_resources, "cloud_resources")
            if ext is not None:
                cloud_resources = ext
        ext_state = extract_json_field(state_resources, "state_resources")
        if ext_state is not None:
            state_resources = ext_state

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
            # Try multiple strategies to handle truncated / malformed JSON often
            # produced by LLM/tool output (ellipses, trailing commas, partial output)
            def try_parse(s: str):
                try:
                    return json.loads(s)
                except Exception:
                    pass
                try:
                    return ast.literal_eval(s)
                except Exception:
                    pass
                return None

            # First attempt: direct parse
            parsed = try_parse(val)
            if parsed is not None:
                return ensure_resource_dict(parsed)

            # Next, clean common truncation patterns: remove ellipses and stray trailing commas
            cleaned = re.sub(r'\.{2,}', '', val)
            cleaned = re.sub(r',\s*(?=[}\]])', '', cleaned)
            parsed = try_parse(cleaned)
            if parsed is not None:
                logger.warning("[WARN] Parsed input after cleaning truncated JSON/ellipses")
                return ensure_resource_dict(parsed)

            # Extract first JSON object or array as a last resort
            m_obj = re.search(r"(\{.*\})", cleaned, flags=re.S)
            if m_obj:
                snippet = m_obj.group(1)
                parsed = try_parse(snippet)
                if parsed is not None:
                    logger.warning("[WARN] Parsed JSON from extracted object snippet")
                    return ensure_resource_dict(parsed)

            m_arr = re.search(r"(\[.*\])", cleaned, flags=re.S)
            if m_arr:
                snippet = m_arr.group(1)
                parsed = try_parse(snippet)
                if parsed is not None:
                    logger.warning("[WARN] Parsed JSON from extracted array snippet")
                    return ensure_resource_dict(parsed)

            logger.error(f"[ERROR] Failed to parse input as JSON after sanitization. Raw value length={len(val)}")
            return {'error': 'Invalid JSON input: parsing failed after sanitization', 'raw_length': len(val)}
        return {'resources': []}

    # Always wrap arrays as dicts with 'resources' key for both state and cloud
    if isinstance(state_resources, list):
        state_resources = {"resources": state_resources}
    if isinstance(cloud_resources, list):
        cloud_resources = {"resources": cloud_resources}

    state_dict = ensure_resource_dict(state_resources)
    cloud_dict = ensure_resource_dict(cloud_resources)
    # Sanitize resource entries: items may be strings (malformed JSON fragments)
    def sanitize_resources_dict(d: dict) -> dict:
        if not isinstance(d, dict):
            return {'resources': []}
        res_list = d.get('resources') or []
        sanitized = []
        for item in res_list:
            # Coerce sets/tuples
            if isinstance(item, (set, tuple)):
                item = list(item)
            # If item is a string, try to parse into dict
            if isinstance(item, str):
                parsed = try_parse(item)
                if isinstance(parsed, dict):
                    item = parsed
                else:
                    # Try to extract an object/array snippet
                    m_obj = re.search(r"(\{.*\})", item, flags=re.S)
                    if m_obj:
                        parsed = try_parse(m_obj.group(1))
                        if isinstance(parsed, dict):
                            item = parsed
                        else:
                            # skip unparseable string entries
                            logger.debug("Skipping unparseable resource entry (string)")
                            continue
                    else:
                        logger.debug("Skipping non-JSON string resource entry")
                        continue
            # If now a dict, filter allowed fields
            if isinstance(item, dict):
                sanitized.append({k: v for k, v in item.items() if k in {"id", "tags", "attributes", "type", "name"}})
            else:
                # Skip unexpected types
                logger.debug(f"Skipping resource entry of unexpected type: {type(item)}")
        return {'resources': sanitized}

    state_dict = sanitize_resources_dict(state_dict)
    cloud_dict = sanitize_resources_dict(cloud_dict)
    result = _compare_resources_impl(state_dict, cloud_dict)
    json_result = json.dumps(result, indent=2)
    print("[DEBUG] FINAL compare_resources JSON output (to LLM):\n" + json_result)
    return json_result


@tool
def compare_resources_raw(raw: str) -> str:
    """Safe wrapper that accepts a single raw string and extracts
    `state_resources` and `cloud_resources` heuristically before calling
    the comparator. This helps when models return complex/embedded JSON
    that is difficult to parse into structured arguments.
    """
    # Local try-parse helpers
    def try_parse(s: str):
        try:
            return json.loads(s)
        except Exception:
            pass
        try:
            return ast.literal_eval(s)
        except Exception:
            pass
        return None

    if not isinstance(raw, str):
        return json.dumps({"error": "compare_resources_raw expects a raw string"})

    parsed = try_parse(raw)
    state = None
    cloud = None
    if isinstance(parsed, dict):
        # Common shapes: {'payload': {...}} or top-level keys
        if 'payload' in parsed and isinstance(parsed['payload'], dict):
            parsed = parsed['payload']
        state = parsed.get('state_resources') or parsed.get('state')
        cloud = parsed.get('cloud_resources') or parsed.get('cloud')

    # Fallback: extract JSON fields by name
    def extract_field(s: str, field: str):
        pat = re.compile(r'"' + re.escape(field) + r'"\s*:\s*')
        m = pat.search(s)
        if not m:
            return None
        idx = m.end()
        while idx < len(s) and s[idx].isspace():
            idx += 1
        if idx >= len(s) or s[idx] not in ('{', '['):
            return None
        open_ch = s[idx]
        close_ch = '}' if open_ch == '{' else ']'
        depth = 0
        end_idx = idx
        for i in range(idx, len(s)):
            ch = s[i]
            if ch == open_ch:
                depth += 1
            elif ch == close_ch:
                depth -= 1
                if depth == 0:
                    end_idx = i + 1
                    break
        snippet = s[idx:end_idx]
        if not snippet:
            return None
        parsed_snip = try_parse(snippet)
        if parsed_snip is not None:
            return parsed_snip
        cleaned = re.sub(r'\.{2,}', '', snippet)
        cleaned = re.sub(r',\s*(?=[}\]])', '', cleaned)
        return try_parse(cleaned)

    if state is None:
        state = extract_field(raw, 'state_resources') or extract_field(raw, 'state')
    if cloud is None:
        cloud = extract_field(raw, 'cloud_resources') or extract_field(raw, 'cloud_resources')

    if state is None or cloud is None:
        # Try to find arrays anywhere and assume first array is state or cloud heuristically
        arrs = re.findall(r'(\[.*?\])', raw, flags=re.S)
        for a in arrs:
            parsed_a = try_parse(a)
            if isinstance(parsed_a, list):
                if state is None:
                    state = parsed_a
                elif cloud is None:
                    cloud = parsed_a
                if state is not None and cloud is not None:
                    break

    if state is None or cloud is None:
        return json.dumps({"error": "Unable to extract state_resources and cloud_resources from raw input"})

    # Normalize to dicts for comparator
    # Coerce sets/tuples to lists, lists to {'resources': ...}, leave dicts as-is
    if isinstance(state, (set, tuple)):
        state = list(state)
    if isinstance(cloud, (set, tuple)):
        cloud = list(cloud)

    if isinstance(state, list):
        state = {'resources': state}
    if isinstance(cloud, list):
        cloud = {'resources': cloud}

    # If values are still unexpected types, return an informative error
    if not isinstance(state, dict) or not isinstance(cloud, dict):
        return json.dumps({"error": "Extracted state/cloud are not JSON objects", "state_type": str(type(state)), "cloud_type": str(type(cloud))})
    # Sanitize resource entries: items may be strings (malformed JSON fragments)
    def sanitize_resources_dict(d: dict) -> dict:
        if not isinstance(d, dict):
            return {'resources': []}
        res_list = d.get('resources') or []
        sanitized = []
        for item in res_list:
            # Coerce sets/tuples
            if isinstance(item, (set, tuple)):
                item = list(item)
            # If item is a string, try to parse into dict
            if isinstance(item, str):
                parsed = try_parse(item)
                if isinstance(parsed, dict):
                    item = parsed
                else:
                    # Try to extract an object/array snippet
                    m_obj = re.search(r"(\{.*\})", item, flags=re.S)
                    if m_obj:
                        parsed = try_parse(m_obj.group(1))
                        if isinstance(parsed, dict):
                            item = parsed
                        else:
                            # skip unparseable string entries
                            logger.debug("Skipping unparseable resource entry (string)")
                            continue
                    else:
                        logger.debug("Skipping non-JSON string resource entry")
                        continue
            # If now a dict, filter allowed fields
            if isinstance(item, dict):
                sanitized.append({k: v for k, v in item.items() if k in {"id", "tags", "attributes", "type", "name"}})
            else:
                # Skip unexpected types
                logger.debug(f"Skipping resource entry of unexpected type: {type(item)}")
        return {'resources': sanitized}

    state = sanitize_resources_dict(state)
    cloud = sanitize_resources_dict(cloud)

    try:
        result = _compare_resources_impl(state, cloud)
        return json.dumps(result, indent=2)
    except Exception as e:
        logger.exception("Error running comparator on extracted payload")
        return json.dumps({"error": f"Comparator failure: {str(e)}"})


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
