"""
base.py — Base class for integration modules.

Defines the interface that all integration modules must implement.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class IntegrationModule(ABC):
    """
    Abstract base class for all integration modules.

    Each integration (e.g., pgvector, Redis, Langfuse) implements this interface
    to provide consistent scaffolding capabilities.

    Example:
        class PgVectorIntegration(IntegrationModule):
            @property
            def name(self) -> str:
                return "pgvector"

            def get_dependencies(self) -> List[str]:
                return ["psycopg2-binary>=2.9.9", "pgvector>=0.2.4"]

            # ... implement other methods
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Integration name (e.g., 'pgvector', 'redis', 'langfuse').

        Must be lowercase, URL-safe, and match the CLI flag name.
        """
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """
        Human-readable name for display (e.g., 'pgvector', 'Redis', 'Langfuse').
        """
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Brief description of the integration (one line).
        """
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """
        Integration category: 'vector_store', 'cache', 'observability', 'loader'.
        """
        pass

    @property
    def version(self) -> str:
        """
        Version when this integration was added (default: "0.1.0").
        """
        return "0.1.0"

    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """
        Return list of pip dependencies required for this integration.

        Returns:
            List of package specifications (e.g., ["redis>=5.0.0", "langchain-redis"])

        Example:
            return ["psycopg2-binary>=2.9.9", "pgvector>=0.2.4"]
        """
        pass

    @abstractmethod
    def get_env_vars(self) -> Dict[str, str]:
        """
        Return dict of environment variables with example values.

        Returns:
            Dict mapping variable names to example values

        Example:
            return {
                "POSTGRES_HOST": "localhost",
                "POSTGRES_PORT": "5432",
                "POSTGRES_DB": "langchain_vectors"
            }
        """
        pass

    @abstractmethod
    def get_template_files(self) -> List[Tuple[str, str]]:
        """
        Return list of (template_path, output_path) tuples for file generation.

        Template paths are relative to cli/ai_agent_builder/templates/integrations/
        Output paths are relative to the project root.

        Returns:
            List of (template_file, output_file) tuples

        Example:
            return [
                ("pgvector/vector_store.py.j2", "src/db/vector_store.py"),
                ("pgvector/schema.sql.j2", "src/db/schema.sql")
            ]
        """
        pass

    @abstractmethod
    def get_test_fixtures(self) -> str:
        """
        Return pytest fixture code for mocking this integration in tests.

        Returns:
            Python code defining pytest fixtures (as a string)

        Example:
            return '''
@pytest.fixture
def mock_pgvector_connection(mocker):
    \"\"\"Mock psycopg2 connection for testing.\"\"\"
    mock_conn = mocker.Mock()
    mocker.patch("psycopg2.connect", return_value=mock_conn)
    return mock_conn
'''
        """
        pass

    def get_prerequisites(self) -> List[str]:
        """
        Return list of prerequisites (external services, setup steps).

        Returns:
            List of prerequisite descriptions (displayed in README)

        Example:
            return [
                "PostgreSQL 15+ installed",
                "pgvector extension: CREATE EXTENSION vector;",
                "Database created: CREATE DATABASE langchain_vectors;"
            ]
        """
        return []

    def get_readme_section(self) -> str:
        """
        Return additional README content specific to this integration.

        Returns:
            Markdown content for README (setup instructions, usage notes)
        """
        sections = []

        # Prerequisites section
        prereqs = self.get_prerequisites()
        if prereqs:
            sections.append(f"### {self.display_name} Setup\n")
            sections.append("**Prerequisites:**\n")
            for prereq in prereqs:
                sections.append(f"- {prereq}\n")
            sections.append("\n")

        # Environment variables section
        env_vars = self.get_env_vars()
        if env_vars:
            sections.append("**Environment Variables:**\n")
            sections.append("Add these to your `.env` file:\n")
            sections.append("```env\n")
            for key, value in env_vars.items():
                sections.append(f"{key}={value}\n")
            sections.append("```\n\n")

        return "".join(sections)

    def post_generate_hook(self, project_path: Path) -> None:
        """
        Optional hook called after files are generated.

        Use this for creating additional directories, running setup commands, etc.

        Args:
            project_path: Absolute path to the generated project directory
        """
        pass

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """
        Check if prerequisites for this integration are met.

        Returns:
            Tuple of (is_valid, error_message)
            - If valid: (True, None)
            - If invalid: (False, "Error description")

        Example:
            # Check if PostgreSQL is accessible
            try:
                import pgvector
                return (True, None)
            except ImportError:
                return (False, "pgvector library not installed")
        """
        return (True, None)
