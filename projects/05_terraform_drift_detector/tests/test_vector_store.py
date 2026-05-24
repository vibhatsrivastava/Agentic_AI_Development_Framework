"""Tests for RAG vector store initialization."""

import pytest
from unittest.mock import Mock
from rag.vector_store import initialize_vector_store, get_retriever


def test_initialize_vector_store_builds_new(tmp_path, mock_embeddings, mocker):
    """Test building new vector store from policy files."""
    # Create temporary policy files
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir()
    (policies_dir / "tags.yaml").write_text("environment: prod\nrequired_tags:\n  - Environment")
    
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "best_practices.md").write_text("# Best Practices\n\nTag all resources.")
    
    # Mock Chroma.from_documents
    mock_vector_store = Mock()
    mock_from_documents = mocker.patch(
        "langchain_chroma.Chroma.from_documents",
        return_value=mock_vector_store
    )
    
    # Mock DirectoryLoader
    mock_policy_doc = Mock(page_content="policy content", metadata={"source": "policies/tags.yaml"})
    mock_docs_doc = Mock(page_content="docs content", metadata={"source": "docs/best_practices.md"})
    
    mock_loader = Mock()
    mock_loader.load.side_effect = [[mock_policy_doc], [mock_docs_doc]]
    mocker.patch("langchain_community.document_loaders.DirectoryLoader", return_value=mock_loader)
    
    # Change to tmp_path directory
    mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    # Initialize vector store
    initialize_vector_store(
        persist_directory=str(tmp_path / "vector_store"),
        force_rebuild=True
    )
    
    # Chroma.from_documents should have been called
    assert mock_from_documents.called


def test_initialize_vector_store_loads_existing(tmp_path, mock_embeddings, mocker):
    """Test loading existing vector store without rebuild."""
    persist_dir = tmp_path / "vector_store"
    persist_dir.mkdir()
    
    # Mock Chroma constructor
    mock_vector_store = Mock()
    mocker.patch("langchain_chroma.Chroma", return_value=mock_vector_store)
    
    # Initialize with existing directory
    vector_store = initialize_vector_store(
        persist_directory=str(persist_dir),
        force_rebuild=False
    )
    
    # Should return mocked vector store
    assert vector_store == mock_vector_store


def test_initialize_vector_store_force_rebuild(tmp_path, mock_embeddings, mocker):
    """Test force rebuild even when vector store exists."""
    persist_dir = tmp_path / "vector_store"
    persist_dir.mkdir()  # Existing directory
    
    # Create temporary policy files
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir()
    (policies_dir / "tags.yaml").write_text("tags: required")
    
    # Mock Chroma.from_documents
    mock_vector_store = Mock()
    mocker.patch("langchain_chroma.Chroma.from_documents", return_value=mock_vector_store)
    
    # Mock DirectoryLoader
    mock_doc = Mock(page_content="content", metadata={"source": "policies/tags.yaml"})
    mock_loader = Mock()
    mock_loader.load.return_value = [mock_doc]
    mocker.patch("langchain_community.document_loaders.DirectoryLoader", return_value=mock_loader)
    
    # Change to tmp_path directory
    mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    # Initialize with force_rebuild=True
    vector_store = initialize_vector_store(
        persist_directory=str(persist_dir),
        force_rebuild=True
    )
    
    # from_documents should have been called (rebuild)
    assert vector_store == mock_vector_store


def test_initialize_vector_store_missing_policies_dir(tmp_path, mock_embeddings, mocker):
    """Test error handling when policies directory doesn't exist."""
    # Mock that policies directory doesn't exist
    mocker.patch("pathlib.Path.exists", side_effect=lambda: False)
    
    with pytest.raises(FileNotFoundError, match="Policies directory not found"):
        initialize_vector_store(persist_directory=str(tmp_path / "vector_store"))


def test_initialize_vector_store_no_documents(tmp_path, mock_embeddings, mocker):
    """Test error handling when no documents found to index."""
    # Create empty policy directory
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir()
    
    # Mock DirectoryLoader returning empty list
    mock_loader = Mock()
    mock_loader.load.return_value = []
    mocker.patch("langchain_community.document_loaders.DirectoryLoader", return_value=mock_loader)
    
    # Change to tmp_path directory
    mocker.patch("pathlib.Path.cwd", return_value=tmp_path)
    mocker.patch("pathlib.Path.exists", return_value=True)
    
    with pytest.raises(ValueError, match="No documents found to index"):
        initialize_vector_store(
            persist_directory=str(tmp_path / "vector_store"),
            force_rebuild=True
        )


def test_get_retriever():
    """Test retriever creation from vector store."""
    mock_vector_store = Mock()
    mock_retriever = Mock()
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    retriever = get_retriever(mock_vector_store, k=5)
    
    # as_retriever should be called with correct parameters
    mock_vector_store.as_retriever.assert_called_once_with(search_kwargs={"k": 5})
    assert retriever == mock_retriever


def test_get_retriever_custom_k():
    """Test retriever with custom k parameter."""
    mock_vector_store = Mock()
    mock_retriever = Mock()
    mock_vector_store.as_retriever.return_value = mock_retriever
    
    get_retriever(mock_vector_store, k=10)
    
    mock_vector_store.as_retriever.assert_called_once_with(search_kwargs={"k": 10})
