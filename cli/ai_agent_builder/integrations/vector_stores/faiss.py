"""
faiss.py — FAISS vector store integration module.

High-performance local vector search from Facebook AI Research.
"""

from typing import Dict, List, Optional, Tuple

from ..base import IntegrationModule


class FAISSIntegration(IntegrationModule):
    """
    FAISS integration for high-performance local vector search.

    Best for CPU-based similarity search with large datasets.
    """

    @property
    def name(self) -> str:
        return "faiss"

    @property
    def display_name(self) -> str:
        return "FAISS"

    @property
    def description(self) -> str:
        return "Facebook AI Similarity Search (high-performance local vectors)"

    @property
    def category(self) -> str:
        return "vector_store"

    def get_dependencies(self) -> List[str]:
        return [
            "faiss-cpu>=1.7.4",
            "langchain-community>=0.0.20",
        ]

    def get_env_vars(self) -> Dict[str, str]:
        return {
            "FAISS_INDEX_PATH": "./faiss_index",
            "FAISS_INDEX_NAME": "langchain_index",
        }

    def get_template_files(self) -> List[Tuple[str, str]]:
        return [
            ("faiss/vector_store.py.j2", "src/db/vector_store.py"),
        ]

    def get_test_fixtures(self) -> str:
        return '''
@pytest.fixture
def mock_faiss_index(mocker):
    """Mock FAISS index for testing."""
    import faiss  # noqa: F401

    mock_index = mocker.Mock()
    mocker.patch("faiss.IndexFlatL2", return_value=mock_index)
    return mock_index


@pytest.fixture
def mock_faiss_store(mocker):
    """Mock FAISS vector store for testing."""
    from langchain_community.vectorstores import FAISS

    mock_store = mocker.Mock(spec=FAISS)
    mock_store.similarity_search.return_value = [
        mocker.Mock(page_content="Sample document 1", metadata={"source": "test1.pdf"}),
        mocker.Mock(page_content="Sample document 2", metadata={"source": "test2.pdf"}),
    ]
    return mock_store
'''

    def get_prerequisites(self) -> List[str]:
        return [
            "FAISS index directory writable (default: ./faiss_index)",
        ]

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """Check if FAISS is installed."""
        try:
            import faiss  # noqa: F401
            return (True, None)
        except ImportError:
            return (False, "faiss-cpu not installed. Run: pip install faiss-cpu")
