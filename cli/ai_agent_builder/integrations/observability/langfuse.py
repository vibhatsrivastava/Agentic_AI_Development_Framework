"""
langfuse.py — Langfuse observability integration module.

**NOTE**: Langfuse tracing is now automatically available via `common/llm_factory`.
This integration module provides **advanced usage patterns only** — basic tracing
requires no scaffolding or integration selection.

**What's already included (no setup needed)**:
- Automatic tracing for all LLM calls (`get_llm()`, `get_chat_llm()`, `get_embeddings()`)
- Configuration via root `.env` (LANGFUSE_ENABLED, LANGFUSE_*_KEY, LANGFUSE_HOST)
- Vault integration support for API keys
- Always-on by default (disable with LANGFUSE_ENABLED=false)

**What this integration adds**:
- Custom trace metadata (session_id, user_id, tags)
- User feedback collection
- Dataset management examples
- Advanced callback configuration

For basic tracing, simply configure root `.env` — no integration needed.
"""

from typing import Dict, List, Optional, Tuple

from ..base import IntegrationModule


class LangfuseIntegration(IntegrationModule):
    """
    Langfuse integration for LLM observability and tracing.

    Provides:
    - Request/response tracing
    - Cost tracking
    - User feedback collection
    - Performance analytics
    """

    @property
    def name(self) -> str:
        return "langfuse"

    @property
    def display_name(self) -> str:
        return "Langfuse"

    @property
    def description(self) -> str:
        return "Advanced Langfuse usage (basic tracing already available via common/)"

    @property
    def category(self) -> str:
        return "observability"

    def get_dependencies(self) -> List[str]:
        # Dependencies now in common/pyproject.toml - no per-project deps needed
        return []

    def get_env_vars(self) -> Dict[str, str]:
        # Variables now in root .env - no project-level env vars needed
        return {}

    def get_template_files(self) -> List[Tuple[str, str]]:
        return [
            ("langfuse/tracing.py.j2", "src/monitoring/tracing.py"),
        ]

    def get_test_fixtures(self) -> str:
        return '''
@pytest.fixture
def mock_langfuse_client(mocker):
    """Mock Langfuse client for testing."""
    mock_client = mocker.Mock()
    mock_client.trace.return_value = mocker.Mock()
    mock_client.generation.return_value = mocker.Mock()
    mocker.patch("langfuse.Langfuse", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_langfuse_callback(mocker):
    """Mock Langfuse callback handler for testing."""
    from langfuse.callback import CallbackHandler

    mock_handler = mocker.Mock(spec=CallbackHandler)
    mocker.patch("langfuse.callback.CallbackHandler", return_value=mock_handler)
    return mock_handler
'''

    def get_prerequisites(self) -> List[str]:
        return [
            "Langfuse is already integrated at common/ level (auto-tracing enabled)",
            "Configure root .env with LANGFUSE_ENABLED, LANGFUSE_*_KEY, LANGFUSE_HOST",
            "This integration provides advanced usage only (custom metadata, datasets, etc.)",
            "See docs/langfuse.md for full setup instructions",
        ]

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """Check if Langfuse is installed."""
        try:
            import langfuse  # noqa: F401
            return (True, None)
        except ImportError:
            return (False, "langfuse not installed. Run: pip install langfuse")
