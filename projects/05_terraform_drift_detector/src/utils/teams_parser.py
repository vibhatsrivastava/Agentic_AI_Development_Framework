"""Parser utility for teams.yaml resource ownership configuration."""

import os
import re
import yaml
from pathlib import Path
from typing import Optional, Dict, Any
from common.utils import get_logger

logger = get_logger(__name__)


def parse_teams_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Parse teams.yaml configuration file.
    
    Args:
        config_path: Path to teams.yaml file (defaults to policies/teams.yaml)
    
    Returns:
        Dictionary with resource_ownership configuration
        
    Raises:
        FileNotFoundError: If teams.yaml doesn't exist
        yaml.YAMLError: If YAML is invalid
    """
    if config_path is None:
        # Default to policies/teams.yaml relative to project root
        project_root = Path(__file__).parent.parent.parent
        config_path = project_root / "policies" / "teams.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"teams.yaml not found at {config_path}")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        if not config or "resource_ownership" not in config:
            logger.warning("teams.yaml missing 'resource_ownership' key, returning empty config")
            return {"resource_ownership": {}}
        
        logger.info(f"Successfully loaded teams.yaml from {config_path}")
        return config
    
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in teams.yaml: {e}")
        raise
    except Exception as e:
        logger.error(f"Error reading teams.yaml: {e}")
        raise


def get_resource_assignee(
    resource_type: str,
    resource_name: str,
    config: Optional[Dict[str, Any]] = None
) -> Optional[str]:
    """
    Determine the GitHub assignee for a resource based on teams.yaml configuration.
    
    Args:
        resource_type: AWS resource type (e.g., "aws_instance" -> "ec2")
        resource_name: Resource name (e.g., "web-prod-01")
        config: Pre-loaded teams.yaml config (loads from file if not provided)
    
    Returns:
        GitHub username with @ prefix, or None if no match
        
    Fallback chain:
        1. Regex pattern match in teams.yaml
        2. Resource type default_owner in teams.yaml
        3. GITHUB_ISSUE_ASSIGNEE environment variable
        4. None (no assignee)
    """
    # Load config if not provided
    if config is None:
        try:
            config = parse_teams_config()
        except (FileNotFoundError, yaml.YAMLError) as e:
            logger.warning(f"Could not load teams.yaml, using fallback: {e}")
            config = {"resource_ownership": {}}
    
    # Normalize resource type (aws_instance -> ec2, aws_db_instance -> rds)
    resource_type_mapping = {
        "aws_instance": "ec2",
        "aws_db_instance": "rds",
        "aws_s3_bucket": "s3",
        "aws_security_group": "security_group",
    }
    normalized_type = resource_type_mapping.get(resource_type, resource_type)
    
    ownership = config.get("resource_ownership", {})
    type_config = ownership.get(normalized_type, {})
    
    # Strategy 1: Try regex pattern matching
    patterns = type_config.get("patterns", [])
    for pattern_entry in patterns:
        pattern = pattern_entry.get("pattern")
        owner = pattern_entry.get("owner")
        
        if pattern and owner:
            try:
                if re.match(pattern, resource_name):
                    logger.info(f"Matched resource '{resource_name}' to pattern '{pattern}' -> {owner}")
                    # Ensure @ prefix
                    return owner if owner.startswith("@") else f"@{owner}"
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}' in teams.yaml: {e}")
                continue
    
    # Strategy 2: Use resource type default_owner
    default_owner = type_config.get("default_owner")
    if default_owner:
        logger.info(f"Using default_owner for type '{normalized_type}': {default_owner}")
        return default_owner if default_owner.startswith("@") else f"@{default_owner}"
    
    # Strategy 3: Use environment variable fallback
    env_assignee = os.getenv("GITHUB_ISSUE_ASSIGNEE")
    if env_assignee:
        logger.info(f"Using GITHUB_ISSUE_ASSIGNEE from environment: {env_assignee}")
        return env_assignee if env_assignee.startswith("@") else f"@{env_assignee}"
    
    # Strategy 4: No assignee
    logger.info(f"No assignee found for {normalized_type}/{resource_name}")
    return None


def validate_teams_config(config: Dict[str, Any]) -> bool:
    """
    Validate teams.yaml configuration structure.
    
    Args:
        config: Parsed teams.yaml configuration
    
    Returns:
        True if valid, False otherwise (logs errors)
    """
    if not isinstance(config, dict):
        logger.error("teams.yaml must be a dictionary")
        return False
    
    if "resource_ownership" not in config:
        logger.error("teams.yaml missing required 'resource_ownership' key")
        return False
    
    ownership = config["resource_ownership"]
    if not isinstance(ownership, dict):
        logger.error("'resource_ownership' must be a dictionary")
        return False
    
    # Validate each resource type configuration
    valid = True
    for resource_type, type_config in ownership.items():
        if not isinstance(type_config, dict):
            logger.error(f"Configuration for '{resource_type}' must be a dictionary")
            valid = False
            continue
        
        # Validate patterns (optional)
        if "patterns" in type_config:
            patterns = type_config["patterns"]
            if not isinstance(patterns, list):
                logger.error(f"'patterns' for '{resource_type}' must be a list")
                valid = False
            else:
                for idx, pattern_entry in enumerate(patterns):
                    if not isinstance(pattern_entry, dict):
                        logger.error(f"Pattern entry {idx} for '{resource_type}' must be a dictionary")
                        valid = False
                    elif "pattern" not in pattern_entry or "owner" not in pattern_entry:
                        logger.error(f"Pattern entry {idx} for '{resource_type}' missing 'pattern' or 'owner'")
                        valid = False
    
    return valid
