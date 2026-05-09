"""
llm_factory.py — Reusable builders for LLM and embedding models via Ollama.

The factory reads configuration from environment variables defined in .env:
    OLLAMA_BASE_URL        — Ollama server endpoint (remote or local)
    OLLAMA_API_KEY         — Bearer token for authenticated servers (leave blank for local)
    OLLAMA_MODEL           — Default LLM model name (e.g. gpt-oss:20b)
    OLLAMA_EMBEDDING_MODEL — Default embedding model name (e.g. nomic-embed-text)

Optional HashiCorp Vault integration:
    When VAULT_ENABLED=true, OLLAMA_API_KEY is fetched from Vault with fallback to .env.
    See docs/vault.md for setup instructions.

Any project can override the model at call time:
    llm      = get_llm(model="llama3.1:8b")
    chat_llm = get_chat_llm(model="llama3.1:8b")
"""

import os
from langchain_ollama import OllamaLLM, ChatOllama, OllamaEmbeddings
from common.vault import get_secret
from common.utils import load_project_env

load_project_env()

_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
_API_KEY = get_secret(vault_key="OLLAMA_API_KEY", env_fallback_key="OLLAMA_API_KEY", default="")
_DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "gpt-oss:20b")
_DEFAULT_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")


def _auth_headers() -> dict:
    """Return Bearer auth headers if an API key is configured."""
    if _API_KEY:
        return {"Authorization": f"Bearer {_API_KEY}"}
    return {}


def get_llm(model: str = None, temperature: float = 0.0) -> OllamaLLM:
    """
    Return a configured OllamaLLM instance for raw string completion chains.

    Use this when working with simple prompt → string output chains (LLMChain,
    RunnableSequence with string prompts), or with tools that expect plain string I/O.

    Args:
        model:       Ollama model name. Defaults to OLLAMA_MODEL env var.
        temperature: Sampling temperature. 0.0 = deterministic.

    Returns:
        OllamaLLM instance ready for chain/agent use.

    Example:
        from common.llm_factory import get_llm
        llm = get_llm()                                    # uses default model
        llm = get_llm(model="llama3.1:8b")                 # override model
        llm = get_llm(model="mistral:7b", temperature=0.7) # creative responses
    """
    return OllamaLLM(
        model=model or _DEFAULT_MODEL,
        base_url=_BASE_URL,
        temperature=temperature,
        client_kwargs={"headers": _auth_headers()},
    )


def get_chat_llm(
    model: str = None,
    temperature: float = 0.0,
    format: str = "",
    num_ctx: int = None,
) -> ChatOllama:
    """
    Return a configured ChatOllama instance for conversational and agentic use.

    Use this when building multi-turn chat apps, LangGraph agents, workflows
    with message history/memory, tool-calling patterns, or structured JSON output.
    Supports OpenAI-compatible message roles (system / human / ai).

    Args:
        model:       Ollama model name. Defaults to OLLAMA_MODEL env var.
        temperature: Sampling temperature. 0.0 = deterministic.
        format:      Set to "json" to enable Ollama's structured JSON output mode.
        num_ctx:     Context window size in tokens. Uses model default if None.

    Returns:
        ChatOllama instance ready for chain/agent use.

    Example:
        from common.llm_factory import get_chat_llm
        chat = get_chat_llm()                                   # default model
        chat = get_chat_llm(model="llama3.1:8b", temperature=0.5)
        chat = get_chat_llm(format="json")                      # JSON output mode
        chat = get_chat_llm(model="llama3.1:8b", num_ctx=8192)  # larger context
    """
    kwargs = dict(
        model=model or _DEFAULT_MODEL,
        base_url=_BASE_URL,
        temperature=temperature,
        client_kwargs={"headers": _auth_headers()},
    )
    if format:
        kwargs["format"] = format
    if num_ctx is not None:
        kwargs["num_ctx"] = num_ctx

    return ChatOllama(**kwargs)


def get_embeddings(model: str = None) -> OllamaEmbeddings:
    """
    Return a configured OllamaEmbeddings instance.

    Args:
        model: Ollama embedding model name. Defaults to OLLAMA_EMBEDDING_MODEL env var.

    Returns:
        OllamaEmbeddings instance ready for RAG / vector store use.

    Example:
        from common.llm_factory import get_embeddings
        embeddings = get_embeddings()
        embeddings = get_embeddings(model="mxbai-embed-large")
    """
    return OllamaEmbeddings(
        model=model or _DEFAULT_EMBEDDING_MODEL,
        base_url=_BASE_URL,
        client_kwargs={"headers": _auth_headers()},
    )
