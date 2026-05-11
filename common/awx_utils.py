"""
awx_utils.py — Helper utilities for AWX integration.

Provides functions for:
- Extracting agent parameters from environment variables
- Formatting output as JSON for AWX parsing
- Validating project structure before execution
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


def extract_agent_params() -> Dict[str, str]:
    """
    Extract agent-specific parameters from environment variables.
    
    AWX injects survey responses and credentials as environment variables.
    This function extracts commonly used parameters for agents.
    
    Returns:
        Dict mapping parameter names to values (all as strings)
        
    Example:
        {
            'city': 'London',
            'github_repo': 'owner/repo',
            'github_issue_number': '42',
            'log_level': 'INFO',
            ...
        }
    """
    params = {}
    
    # Common agent parameters (from AWX surveys)
    param_keys = [
        # Weather agent
        "CITY",
        # GitHub agent
        "GITHUB_REPO",
        "GITHUB_ISSUE_NUMBER",
        # Generic parameters
        "LOG_LEVEL",
        # Custom parameters (agents can read any env var)
        "CUSTOM_PARAM_1",
        "CUSTOM_PARAM_2",
    ]
    
    for key in param_keys:
        value = os.getenv(key)
        if value is not None and value != "":
            # Store with lowercase key for consistency
            params[key.lower()] = value
    
    return params


def format_awx_output(result: Dict[str, Any]) -> str:
    """
    Format agent result as JSON string for AWX parsing.
    
    Args:
        result: Agent execution result dict
        
    Returns:
        JSON string formatted for AWX output
        
    Example input:
        {
            'status': 'success',
            'result': 'Weather in London: 15°C',
            'metadata': {'agent': '03_weather_reporting_agent', ...}
        }
        
    Example output:
        '{"status":"success","result":"Weather in London: 15°C",...}'
    """
    try:
        return json.dumps(result, indent=2, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        # Fallback for non-serializable objects
        return json.dumps({
            "status": "error",
            "error": f"Failed to serialize output: {str(e)}",
            "result": str(result)
        })


def validate_project_structure(project_name: str, repo_root: Path) -> None:
    """
    Validate that project structure is correct before execution.
    
    Args:
        project_name: Project directory name
        repo_root: Path to repository root
        
    Raises:
        FileNotFoundError: If project structure is invalid
    """
    project_path = repo_root / "projects" / project_name
    
    if not project_path.exists():
        raise FileNotFoundError(
            f"Project directory not found: {project_path}\n"
            f"Expected: projects/{project_name}"
        )
    
    src_path = project_path / "src"
    if not src_path.exists():
        raise FileNotFoundError(
            f"Source directory not found: {src_path}\n"
            f"Expected: projects/{project_name}/src"
        )
    
    main_path = src_path / "main.py"
    if not main_path.exists():
        raise FileNotFoundError(
            f"Main module not found: {main_path}\n"
            f"Expected: projects/{project_name}/src/main.py"
        )
    
    # Validate venv exists (AWX should have set this up)
    venv_path = project_path / ".venv"
    if not venv_path.exists():
        raise FileNotFoundError(
            f"Virtual environment not found: {venv_path}\n"
            f"Run setup before executing agent from AWX:\n"
            f"  cd {project_path} && uv venv .venv && uv pip install -r requirements.txt"
        )


def load_env_from_dict(env_dict: Dict[str, str]) -> None:
    """
    Load environment variables from a dictionary.
    
    This is useful for programmatically injecting AWX credentials
    and survey responses as environment variables before agent execution.
    
    Args:
        env_dict: Dictionary of environment variable key-value pairs
        
    Example:
        awx_creds = {
            'OLLAMA_BASE_URL': 'http://ollama:11434',
            'OLLAMA_API_KEY': 'token123',
        }
        load_env_from_dict(awx_creds)
        # Now os.getenv('OLLAMA_BASE_URL') returns 'http://ollama:11434'
    """
    for key, value in env_dict.items():
        if value is not None:
            os.environ[key] = str(value)
