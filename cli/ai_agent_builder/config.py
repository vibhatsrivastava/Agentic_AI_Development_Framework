"""
config.py — Configuration and constants for AI Agent Builder CLI.

Defines base architectures, project patterns, and default configurations.
"""

from pathlib import Path

# Package root directory
CLI_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = Path(__file__).parent / "templates"

# Project naming pattern
PROJECT_NAME_PATTERN = r"^\d{2}_[a-z][a-z0-9_]*$"
PROJECT_NAME_EXAMPLE = "05_my_project_name"

# Base architectures supported
BASE_ARCHITECTURES = {
    "lcel": {
        "name": "LCEL Chain",
        "description": "LangChain Expression Language chain (simple prompt → LLM → output)",
        "template_dir": "lcel",
        "default_imports": [
            "from langchain_core.prompts import PromptTemplate",
            "from langchain_core.output_parsers import StrOutputParser",
            "from common.llm_factory import get_llm",
        ],
    },
    "langgraph": {
        "name": "LangGraph Agent",
        "description": "Stateful multi-agent system with LangGraph",
        "template_dir": "langgraph",
        "default_imports": [
            "from langgraph.prebuilt import create_react_agent",
            "from langchain_core.tools import tool",
            "from common.llm_factory import get_chat_llm",
        ],
    },
    "custom": {
        "name": "Custom (Minimal)",
        "description": "Minimal scaffold with only sys.path setup and common/ imports",
        "template_dir": "custom",
        "default_imports": [
            "from common.llm_factory import get_llm, get_chat_llm",
            "from common.utils import get_logger",
        ],
    },
}

# Default environment variables (always included in .env.example)
DEFAULT_ENV_VARS = {
    "OLLAMA_BASE_URL": "http://localhost:11434",
    "OLLAMA_API_KEY": "",
    "OLLAMA_MODEL": "gpt-oss:20b",
    "OLLAMA_EMBEDDING_MODEL": "nomic-embed-text",
    "LOG_LEVEL": "INFO",
    "VAULT_ENABLED": "false",
    "VAULT_ADDR": "http://vault.example.com:8200",
    "VAULT_TOKEN": "your_vault_token_here",
    "VAULT_SECRET_PATH": "ollama",
    "VAULT_MOUNT_POINT": "secret",
}

# Default dependencies (always included in requirements.txt)
BASE_DEPENDENCIES = [
    "# Base dependencies (inherited from requirements-base.txt)",
    "# Only add project-specific dependencies below",
]

# Test fixtures template (always included in conftest.py)
BASE_TEST_FIXTURES = """
import pytest
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))


@pytest.fixture
def sample_prompt():
    \"\"\"Sample prompt for testing.\"\"\"
    return "What is artificial intelligence?"


@pytest.fixture
def expected_response_keywords():
    \"\"\"Keywords expected in LLM response (for validation).\"\"\"
    return ["AI", "intelligence", "artificial", "machine", "learning"]
"""

# Project structure template
PROJECT_STRUCTURE = {
    "dirs": [
        "src",
        "tests",
    ],
    "files": {
        "src/main.py": "main.py.j2",
        "tests/conftest.py": "conftest.py.j2",
        "tests/test_main.py": "test_main.py.j2",
        "requirements.txt": "requirements.txt.j2",
        # .env.example removed — only created by _generate_env_file() when integrations exist
        # All base variables live in repo-root .env (found via load_dotenv())
        "README.md": "README.md.j2",
    },
}

# pytest configuration (for reference)
PYTEST_CONFIG = {
    "min_coverage": 90,
    "test_patterns": ["test_*.py"],
    "markers": ["unit", "integration"],
}


def get_project_number(project_name: str) -> str:
    """
    Extract project number from project name.

    Args:
        project_name: Project name (e.g., "05_my_project")

    Returns:
        Project number (e.g., "05")

    Raises:
        ValueError: If project name doesn't match pattern
    """
    import re

    match = re.match(r"^(\d{2})_", project_name)
    if not match:
        raise ValueError(
            f"Project name '{project_name}' doesn't match pattern. "
            f"Expected: {PROJECT_NAME_EXAMPLE}"
        )

    return match.group(1)


def get_project_description(project_name: str) -> str:
    """
    Generate a human-readable project description from the name.

    Args:
        project_name: Project name (e.g., "05_rag_pgvector")

    Returns:
        Description (e.g., "RAG with pgvector")
    """
    # Remove number prefix
    name_without_number = project_name.split("_", 1)[1] if "_" in project_name else project_name

    # Replace underscores with spaces and title case
    return name_without_number.replace("_", " ").title()
