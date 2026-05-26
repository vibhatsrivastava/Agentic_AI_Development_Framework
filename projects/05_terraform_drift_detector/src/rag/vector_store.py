"""RAG Vector Store initialization for Terraform policy documents."""

from pathlib import Path
from langchain_community import document_loaders
from langchain_text_splitters import RecursiveCharacterTextSplitter
import langchain_chroma
from common import llm_factory
from common.utils import get_logger

logger = get_logger(__name__)


def initialize_vector_store(
    persist_directory: str = "./vector_store",
    force_rebuild: bool = False,
    collection_name: str = "terraform_policies"
) -> langchain_chroma.Chroma:
    """
    Initialize Chroma vector store from policy files and documentation.
    
    Indexes:
    - Policy files from policies/*.yaml
    - Best practices from docs/*.md
    
    Args:
        persist_directory: Directory to store vector database
        force_rebuild: If True, rebuild even if vector store exists
        collection_name: Name of the Chroma collection
    
    Returns:
        Chroma vector store instance
    """
    persist_path = Path(persist_directory)
    
    # Simple in-process cache to avoid reloading/rebuilding vector stores
    # during the lifetime of the process. Keyed by persist_directory so
    # multiple stores can be used for different projects.
    global _VECTOR_STORE_CACHE
    try:
        _VECTOR_STORE_CACHE
    except NameError:
        _VECTOR_STORE_CACHE = {}

    # Load existing vector store if available on disk and not forcing rebuild
    if persist_path.exists() and not force_rebuild:
        if persist_directory in _VECTOR_STORE_CACHE:
            logger.info(f"Reusing cached vector store for {persist_directory}")
            return _VECTOR_STORE_CACHE[persist_directory]
        logger.info(f"Loading existing vector store from {persist_directory}")
        try:
            store = langchain_chroma.Chroma(
                persist_directory=persist_directory,
                embedding_function=llm_factory.get_embeddings(),
                collection_name=collection_name,
            )
            _VECTOR_STORE_CACHE[persist_directory] = store
            return store
        except Exception as e:
            logger.warning(f"Failed to load existing vector store: {e}. Rebuilding...")
    
    # Build new vector store
    logger.info("Building new vector store from policy files and documentation...")
    
    # Load policy files (YAML)
    base_dir = Path.cwd()
    policies_dir = base_dir / "policies"
    if not policies_dir.exists():
        raise FileNotFoundError(f"Policies directory not found: {policies_dir}")
    
    policy_loader = document_loaders.DirectoryLoader(
        str(policies_dir),
        glob="**/*.yaml",
        show_progress=True,
    )
    policy_docs = policy_loader.load()
    logger.info(f"Loaded {len(policy_docs)} policy documents")
    
    # Load best practices documentation (Markdown)
    docs_dir = base_dir / "docs"
    best_practice_docs = []
    if docs_dir.exists():
        try:
            docs_loader = document_loaders.DirectoryLoader(
                str(docs_dir),
                glob="**/*.md",
                show_progress=True,
            )
            best_practice_docs = docs_loader.load()
            logger.info(f"Loaded {len(best_practice_docs)} documentation files")
        except (FileNotFoundError, PermissionError, ValueError) as e:
            logger.warning(
                f"Failed to load documentation files from {docs_dir}: {type(e).__name__}: {e}"
            )
    else:
        logger.warning(f"Documentation directory not found: {docs_dir}")
    
    # Combine all documents
    all_docs = policy_docs + best_practice_docs
    
    if not all_docs:
        raise ValueError("No documents found to index. Check policies/ and docs/ directories.")
    
    # Split documents into chunks for precise retrieval
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,  # Small chunks for precise policy citations
        chunk_overlap=50,
        length_function=len,
    )
    chunks = splitter.split_documents(all_docs)
    logger.info(f"Split into {len(chunks)} chunks")
    
    # Create vector store
    vector_store = langchain_chroma.Chroma.from_documents(
        documents=chunks,
        embedding=llm_factory.get_embeddings(),
        persist_directory=persist_directory,
        collection_name=collection_name,
    )
    
    logger.info(f"Vector store created with {len(chunks)} chunks")
    logger.info(f"Persisted to: {persist_directory}")

    # Cache and return
    _VECTOR_STORE_CACHE[persist_directory] = vector_store
    return vector_store


def get_retriever(vector_store: langchain_chroma.Chroma, k: int = 5):
    """
    Get a retriever from the vector store.
    
    Args:
        vector_store: Chroma vector store instance
        k: Number of documents to retrieve
    
    Returns:
        Retriever instance configured for policy search
    """
    return vector_store.as_retriever(search_kwargs={"k": k})
