"""
env_manager.py — Environment variable management for project scaffolding.

Handles .env file generation, Vault integration, and environment validation.
"""

from pathlib import Path
from typing import Dict, List

from dotenv import dotenv_values

from .config import DEFAULT_ENV_VARS


class EnvManager:
    """
    Manages environment variables for scaffolded projects.

    Features:
    - Generate .env.example files with integration-specific variables
    - Validate .env files against required variables
    - Merge default + integration-specific environment variables

    Example:
        env_mgr = EnvManager()
        env_vars = env_mgr.get_env_vars(integrations=["pgvector", "langfuse"])
        env_mgr.write_env_example(project_path, env_vars)
    """

    def __init__(self):
        """Initialize environment manager."""
        self.default_vars = DEFAULT_ENV_VARS.copy()

    def get_env_vars(self, integrations: List[str]) -> Dict[str, str]:
        """
        Get all environment variables for a project with integrations.

        Args:
            integrations: List of integration names

        Returns:
            Dictionary of environment variables with example values
        """
        from .integrations import get_integration

        # Start with default variables
        env_vars = self.default_vars.copy()

        # Add integration-specific variables
        for integration_name in integrations:
            integration = get_integration(integration_name)
            if integration:
                integration_vars = integration.get_env_vars()
                env_vars.update(integration_vars)

        return env_vars

    def write_env_example(
        self,
        project_path: Path,
        integrations: List[str],
    ) -> Path:
        """
        Write .env.example file containing ONLY integration-specific variables.

        ⚠️ IMPORTANT: This file should ONLY exist when integrations are selected.
        Base Ollama/Vault variables are intentionally excluded — they live in
        the repo-root .env and are found automatically via load_project_env().
        
        The generated file is a template for creating a project-level .env file
        with integration-specific variables (GITHUB_*, REDIS_*, PGVECTOR_*, etc.).
        
        Users should:
        1. Copy this file to .env in the project directory
        2. Configure the integration-specific values
        3. Common variables (OLLAMA_*, VAULT_*) remain in repo-root .env only

        Args:
            project_path: Path to project directory
            integrations: List of integration names whose variables to include

        Returns:
            Path to created .env.example file
        """
        from .integrations import get_integration

        # Collect only integration-specific variables
        integration_vars: Dict[str, str] = {}
        for integration_name in integrations:
            integration = get_integration(integration_name)
            if integration:
                integration_vars.update(integration.get_env_vars())

        env_file = project_path / ".env.example"

        with open(env_file, "w", encoding="utf-8") as f:
            f.write("# Integration-specific environment variables\n")
            f.write("# Copy this file to .env in this project directory and configure these values.\n")
            f.write("# Common variables (OLLAMA_*, VAULT_*, LOG_LEVEL) remain in repo-root .env only.\n\n")

            for key in sorted(integration_vars.keys()):
                f.write(f"{key}={integration_vars[key]}\n")
            f.write("\n")

        return env_file

    def validate_env_file(
        self,
        env_file: Path,
        required_vars: List[str]
    ) -> tuple[bool, List[str]]:
        """
        Validate that .env file contains all required variables.

        Args:
            env_file: Path to .env file
            required_vars: List of required variable names

        Returns:
            Tuple of (is_valid, missing_vars)
        """
        if not env_file.exists():
            return (False, required_vars)

        # Load .env file
        env_values = dotenv_values(env_file)

        # Check for missing variables
        missing = [var for var in required_vars if var not in env_values]

        return (len(missing) == 0, missing)

    def get_required_vars(self, integrations: List[str]) -> List[str]:
        """
        Get list of required environment variables for integrations.

        Args:
            integrations: List of integration names

        Returns:
            List of required variable names
        """
        from .integrations import get_integration

        # Always require base Ollama variables
        required = ["OLLAMA_BASE_URL", "OLLAMA_MODEL"]

        # Add integration-specific required variables
        for integration_name in integrations:
            integration = get_integration(integration_name)
            if integration:
                env_vars = integration.get_env_vars()
                # Assume all integration env vars are required
                required.extend(env_vars.keys())

        return list(set(required))  # Remove duplicates

    def merge_env_files(self, base_env: Path, project_env: Path) -> Dict[str, str]:
        """
        Merge base .env with project-specific .env.

        Base variables are used unless overridden in project .env.

        Args:
            base_env: Path to base .env file (repo root)
            project_env: Path to project-specific .env file

        Returns:
            Merged dictionary of environment variables
        """
        # Load base environment
        base_vars = dotenv_values(base_env) if base_env.exists() else {}

        # Load project environment
        project_vars = dotenv_values(project_env) if project_env.exists() else {}

        # Merge (project vars override base)
        merged = base_vars.copy()
        merged.update(project_vars)

        return merged

    def format_env_file(self, env_vars: Dict[str, str]) -> str:
        """
        Format environment variables as .env file content.

        Args:
            env_vars: Dictionary of environment variables

        Returns:
            Formatted .env file content
        """
        lines = []

        for key, value in sorted(env_vars.items()):
            # Handle multiline values (quote them)
            if "\n" in value:
                value = f'"{value}"'

            lines.append(f"{key}={value}")

        return "\n".join(lines) + "\n"
