"""
template_renderer.py — Jinja2 template rendering for project scaffolding.

Renders project files from templates with context variables.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader

from .config import TEMPLATES_DIR


class TemplateRenderer:
    """
    Renders Jinja2 templates for project scaffolding.

    Attributes:
        env: Jinja2 Environment configured with template loaders
        templates_dir: Path to templates directory

    Example:
        renderer = TemplateRenderer()
        content = renderer.render_template(
            "lcel/main.py.j2",
            context={
                "project_name": "05_sentiment_analysis",
                "integrations": ["langfuse"],
                "architecture": "lcel"
            }
        )
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template renderer.

        Args:
            templates_dir: Path to templates directory (defaults to config.TEMPLATES_DIR)
        """
        self.templates_dir = templates_dir or TEMPLATES_DIR

        # Create Jinja2 environment with file system loader
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

        # Register custom filters
        self.env.filters["snake_case"] = self._snake_case
        self.env.filters["title_case"] = self._title_case
        self.env.filters["project_description"] = self._project_description

    def render_template(self, template_path: str, context: Dict[str, Any]) -> str:
        """
        Render a template with the given context.

        Args:
            template_path: Path to template relative to templates_dir (e.g., "lcel/main.py.j2")
            context: Dictionary of template variables

        Returns:
            Rendered template content as string

        Raises:
            TemplateNotFound: If template file doesn't exist
            jinja2.TemplateError: If template rendering fails
        """
        template = self.env.get_template(template_path)
        return template.render(**context)

    def render_string(self, template_str: str, context: Dict[str, Any]) -> str:
        """
        Render a template string (not from file).

        Args:
            template_str: Template content as string
            context: Dictionary of template variables

        Returns:
            Rendered content as string
        """
        template = self.env.from_string(template_str)
        return template.render(**context)

    def template_exists(self, template_path: str) -> bool:
        """
        Check if a template file exists.

        Args:
            template_path: Path to template relative to templates_dir

        Returns:
            True if template exists, False otherwise
        """
        full_path = self.templates_dir / template_path
        return full_path.exists()

    def list_templates(self, pattern: str = "**/*.j2") -> list[str]:
        """
        List all templates matching a pattern.

        Args:
            pattern: Glob pattern for template files (default: "**/*.j2")

        Returns:
            List of template paths relative to templates_dir
        """
        matches = self.templates_dir.glob(pattern)
        return [
            str(p.relative_to(self.templates_dir))
            for p in matches
            if p.is_file()
        ]

    @staticmethod
    def _snake_case(s: str) -> str:
        """
        Convert string to snake_case.

        Filter usage: {{ variable | snake_case }}
        """
        return s.lower().replace("-", "_").replace(" ", "_")

    @staticmethod
    def _title_case(s: str) -> str:
        """
        Convert string to Title Case.

        Filter usage: {{ variable | title_case }}
        """
        return s.replace("_", " ").replace("-", " ").title()

    @staticmethod
    def _project_description(project_name: str) -> str:
        """
        Generate human-readable description from project name.

        Filter usage: {{ project_name | project_description }}

        Example:
            "05_rag_pgvector" → "RAG with pgvector"
        """
        # Remove number prefix
        name = project_name.split("_", 1)[1] if "_" in project_name else project_name

        # Replace underscores with spaces and title case
        return name.replace("_", " ").title()


def get_template_context(
    project_name: str,
    project_number: str,
    architecture: str,
    integrations: list[str],
    **kwargs
) -> Dict[str, Any]:
    """
    Build template context dictionary with common variables.

    Args:
        project_name: Full project name (e.g., "05_sentiment_analysis")
        project_number: Project number (e.g., "05")
        architecture: Base architecture ("lcel", "langgraph", "custom")
        integrations: List of integration names (e.g., ["pgvector", "langfuse"])
        **kwargs: Additional context variables

    Returns:
        Dictionary of template variables

    Example:
        context = get_template_context(
            project_name="05_sentiment_analysis",
            project_number="05",
            architecture="lcel",
            integrations=["langfuse"],
            author="John Doe"
        )
    """
    from .config import BASE_ARCHITECTURES, get_project_description

    context = {
        "project_name": project_name,
        "project_number": project_number,
        "project_description": get_project_description(project_name),
        "architecture": architecture,
        "architecture_name": BASE_ARCHITECTURES[architecture]["name"],
        "integrations": integrations,
        "has_integrations": len(integrations) > 0,
        # Integration category flags (for conditional template rendering)
        "has_vector_store": any(i in ["chroma", "pgvector", "faiss", "pinecone", "weaviate", "qdrant"] for i in integrations),
        "has_cache": any(i in ["redis"] for i in integrations),
        "has_observability": any(i in ["langfuse", "langsmith"] for i in integrations),
        "has_pdf_loader": "pdf" in integrations,
        "has_web_scraper": "web" in integrations,
    }

    # Merge additional kwargs
    context.update(kwargs)

    return context
