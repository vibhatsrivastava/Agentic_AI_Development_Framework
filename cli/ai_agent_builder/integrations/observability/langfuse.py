"""
langfuse.py — Langfuse observability integration module.

Open-source LLM tracing, cost tracking, and user feedback.
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
        return "Open-source LLM tracing and observability platform"

    @property
    def category(self) -> str:
        return "observability"

    def get_dependencies(self) -> List[str]:
        return [
            "langfuse>=2.0.0",
            "langchain-langfuse>=2.0.0",
        ]

    def get_env_vars(self) -> Dict[str, str]:
        return {
            "LANGFUSE_PUBLIC_KEY": "pk-lf-...",
            "LANGFUSE_SECRET_KEY": "sk-lf-...",
            "LANGFUSE_HOST": "https://cloud.langfuse.com",  # or self-hosted URL
        }

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
            "Langfuse account created (cloud.langfuse.com or self-hosted)",
            "Project created in Langfuse dashboard",
            "API keys generated (public and secret keys)",
        ]

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """Check if Langfuse is installed."""
        try:
            import langfuse  # noqa: F401
            return (True, None)
        except ImportError:
            return (False, "langfuse not installed. Run: pip install langfuse")
