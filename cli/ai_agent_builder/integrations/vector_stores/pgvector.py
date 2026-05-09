"""
pgvector.py — PostgreSQL pgvector integration module.

Production-grade vector store using PostgreSQL + pgvector extension.
"""

from typing import Dict, List, Optional, Tuple

from ..base import IntegrationModule


class PgVectorIntegration(IntegrationModule):
    """
    pgvector integration for PostgreSQL vector storage.

    Prerequisites:
    - PostgreSQL 15+ installed
    - pgvector extension enabled
    - Database created
    """

    @property
    def name(self) -> str:
        return "pgvector"

    @property
    def display_name(self) -> str:
        return "pgvector"

    @property
    def description(self) -> str:
        return "PostgreSQL vector store with pgvector extension (production-ready)"

    @property
    def category(self) -> str:
        return "vector_store"

    def get_dependencies(self) -> List[str]:
        return [
            "psycopg2-binary>=2.9.9",
            "pgvector>=0.2.4",
            "langchain-postgres>=0.0.6",
        ]

    def get_env_vars(self) -> Dict[str, str]:
        return {
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DB": "langchain_vectors",
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "your_password_here",
            "VECTOR_DIMENSION": "1536",  # nomic-embed-text dimension
        }

    def get_template_files(self) -> List[Tuple[str, str]]:
        return [
            ("pgvector/vector_store.py.j2", "src/db/vector_store.py"),
            ("pgvector/schema.sql.j2", "src/db/schema.sql"),
        ]

    def get_test_fixtures(self) -> str:
        return '''
@pytest.fixture
def mock_pgvector_connection(mocker):
    """Mock psycopg2 connection for testing."""
    mock_conn = mocker.Mock()
    mock_cursor = mocker.Mock()
    mock_conn.cursor.return_value = mock_cursor
    mocker.patch("psycopg2.connect", return_value=mock_conn)
    return mock_conn


@pytest.fixture
def mock_pgvector_store(mocker):
    """Mock PGVector store for testing."""
    from langchain_postgres import PGVector

    mock_store = mocker.Mock(spec=PGVector)
    mock_store.similarity_search.return_value = [
        mocker.Mock(page_content="Sample document 1", metadata={"source": "test1.pdf"}),
        mocker.Mock(page_content="Sample document 2", metadata={"source": "test2.pdf"}),
    ]
    return mock_store
'''

    def get_prerequisites(self) -> List[str]:
        return [
            "PostgreSQL 15+ installed and running",
            "pgvector extension: `CREATE EXTENSION vector;`",
            "Database created: `CREATE DATABASE langchain_vectors;`",
            "Connection credentials configured in .env",
        ]

    def validate_prerequisites(self) -> Tuple[bool, Optional[str]]:
        """Check if pgvector dependencies are installed."""
        try:
            import pgvector  # noqa: F401
            import psycopg2  # noqa: F401
            return (True, None)
        except ImportError as e:
            return (False, f"Missing dependency: {e.name}. Run: pip install psycopg2-binary pgvector")
