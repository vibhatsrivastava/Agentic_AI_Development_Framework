"""
chroma.py — Chroma vector store integration module.

Local vector database ideal for development and small-scale deployments.
"""

from typing import Dict, List, Optional, Tuple

from ..base import IntegrationModule


class ChromaIntegration(IntegrationModule):
    """
    Chroma integration for local vector storage.

    Best for development and prototyping with persistent local storage.
    """

    @property
    def name(self) -> str:
        return "chroma"

    @property
    def display_name(self) -> str:
        return "Chroma"

    @property
    def description(self) -> str:
        return "Local vector database (ideal for development and prototyping)"

    @property
    def category(self) -> str:
        return "vector_store"

    def get_dependencies(self) -> List[str]:
        return [
            "chromadb>=0.4.22",
            "langchain-chroma>=0.1.0",
        ]

    def get_env_vars(self) -> Dict[str, str]:
        return {
            "CHROMA_PERSIST_DIR": "./chroma_db",
            "CHROMA_COLLECTION_NAME": "langchain_collection",
        }

    def get_template_files(self) -> List[Tuple[str, str]]:
        return [
            ("chroma/vector_store.py.j2", "src/db/vector_store.py"),
        ]

    def get_test_fixtures(self) -> str:
        return '''
@pytest.fixture
def mock_chroma_client(mocker):
    """Mock Chroma client for testing."""
    mock_client = mocker.Mock()
    mock_collection = mocker.Mock()
    mock_client.get_or_create_collection.return_value = mock_collection
    mocker.patch("chromadb.Client", return_value=mock_client)
    return mock_client


@pytest.fixture
def mock_chroma_store(mocker):
    """Mock Chroma vector store for testing."""
    from langchain_chroma import Chroma

    mock_store = mocker.Mock(spec=Chroma)
    mock_store.similarity_search.return_value = [
        mocker.Mock(page_content="Sample document 1", metadata={"source": "test1.pdf"}),
        mocker.Mock(page_content="Sample document 2", metadata={"source": "test2.pdf"}),
    ]
    return mock_store
'''

    def get_prerequisites(self) -> List[str]:
        return [
            "Chroma persist directory writable (default: ./chroma_db)",
        ]

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """Check if Chroma is installed."""
        try:
            import chromadb  # noqa: F401
            return (True, None)
        except ImportError:
            return (False, "chromadb not installed. Run: pip install chromadb")
