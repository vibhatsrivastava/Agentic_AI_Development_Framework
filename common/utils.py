"""
utils.py — Common helper utilities shared across projects.
"""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

load_dotenv()


def load_project_env(project_dir: Path = None):
    """
    Load environment variables hierarchically:
    1. Root .env (common variables: OLLAMA_*, VAULT_*, LOG_LEVEL)
    2. Project .env if exists (integration variables: GITHUB_*, REDIS_*, etc.)
    
    Project values override root values, allowing per-project customization.
    
    This enables a two-tier system:
    - Simple projects use only root .env (no project .env needed)
    - Integration projects add project .env for integration-specific variables
    
    Args:
        project_dir: Path to project directory (default: current working directory)
    
    Example:
        # In project main.py
        from common.utils import load_project_env
        load_project_env()  # Loads root .env + project .env if exists
        
        # Now use require_env() for any variable
        github_token = require_env("GITHUB_TOKEN")  # May be in project .env
        ollama_url = require_env("OLLAMA_BASE_URL")   # From root .env
    """
    if project_dir is None:
        project_dir = Path.cwd()
    
    # Find root .env by searching upward from project directory
    # Stop at the first .env that's NOT the project .env
    current = project_dir.resolve()
    root_env_path = None
    
    # Search upward for root .env (skipping project .env if it exists)
    while current.parent != current:  # Until we reach filesystem root
        potential_env = current / ".env"
        if potential_env.exists() and potential_env != (project_dir / ".env"):
            root_env_path = potential_env
            break
        current = current.parent
    
    # Load root .env (common variables)
    if root_env_path and root_env_path.exists():
        load_dotenv(root_env_path)
    
    # Load project .env (integration variables) if exists
    project_env = project_dir / ".env"
    if project_env.exists():
        load_dotenv(project_env, override=True)


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger.

    Args:
        name: Logger name, typically __name__ from the calling module.

    Example:
        from common.utils import get_logger
        logger = get_logger(__name__)
        logger.info("Starting...")
    """
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=getattr(logging, level, logging.INFO),
        force=True,  # Reconfigure even if handlers already exist (Python 3.8+)
    )
    return logging.getLogger(name)


def require_env(key: str) -> str:
    """
    Return an environment variable value, raising a clear error if missing.

    Args:
        key: Environment variable name.

    Raises:
        EnvironmentError: If the variable is not set or empty.

    Example:
        base_url = require_env("OLLAMA_BASE_URL")
    """
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in the value."
        )
    return value


def load_env_from_dict(env_dict: dict[str, str]) -> None:
    """
    Load environment variables from a dictionary.
    
    This is useful for programmatically injecting configuration values
    (e.g., from AWX credentials) as environment variables before agent execution.
    
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
