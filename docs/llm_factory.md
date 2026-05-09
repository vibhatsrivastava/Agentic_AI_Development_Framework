# Common LLM Factory

All projects share a central `common/llm_factory.py` that provides three builder functions. Import the one that fits your use case — no boilerplate, no repeated configuration.

---

## Table of Contents

- [Overview](#overview)
- [Builder Functions](#builder-functions)
- [get_llm() — Raw String Completion](#get_llm--raw-string-completion)
- [get_chat_llm() — Conversational & Agentic](#get_chat_llm--conversational--agentic)
- [get_embeddings() — Semantic Search & RAG](#get_embeddings--semantic-search--rag)
- [Advanced Usage](#advanced-usage)

---

## Overview

The LLM Factory provides three builder functions that handle all the configuration boilerplate for you:

| Builder | Returns | Use When |
|---|---|---|
| `get_llm()` | `OllamaLLM` | Simple string chains, single-turn prompts |
| `get_chat_llm()` | `ChatOllama` | Agents, memory, tool-calling, JSON mode |
| `get_embeddings()` | `OllamaEmbeddings` | RAG, vector stores, similarity search |

All three read `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, and `OLLAMA_MODEL` from your `.env`. The `model` argument overrides the env default for that call only.

**Features:**
- Automatic credential retrieval from `.env` or [HashiCorp Vault](vault.md)
- Zero-configuration defaults for rapid prototyping
- Override any parameter (model, temperature, context window) per call
- Consistent error handling and logging

---

## Builder Functions

### `get_llm()` — Raw String Completion

Best for simple prompt → string output chains with no message history.

**Use Cases:**
- Single-turn question answering
- Text summarization
- Simple text generation tasks
- No conversation context needed

**Example:**

```python
from common.llm_factory import get_llm
from langchain_core.prompts import PromptTemplate

llm = get_llm()  # uses OLLAMA_MODEL from .env; add model= or temperature= to override

prompt = PromptTemplate.from_template("Summarise the following in one sentence:\n{text}")
chain = prompt | llm

result = chain.invoke({"text": "LangChain is a framework for building LLM-powered applications."})
print(result)
# → "LangChain is a framework that simplifies building applications powered by large language models."
```

**Parameters:**
```python
get_llm(
    model: Optional[str] = None,       # Overrides OLLAMA_MODEL from .env
    temperature: float = 0.7,          # Creativity level (0.0-1.0)
    **kwargs                           # Any additional OllamaLLM parameters
)
```

---

### `get_chat_llm()` — Conversational & Agentic

Required for multi-turn conversations, LangGraph agents, tool calling, and structured JSON output.
Uses OpenAI-compatible message roles (`system` / `human` / `ai`).

**Use Cases:**
- Multi-turn conversations with memory
- ReAct agents and tool calling
- LangGraph workflows
- Structured JSON output
- Complex agentic workflows

**Example:**

```python
from common.llm_factory import get_chat_llm
from langchain_core.prompts import ChatPromptTemplate

chat = get_chat_llm()  # uses OLLAMA_MODEL from .env; supports format="json" and num_ctx=

prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant that answers concisely."),
    ("human", "{question}"),
])
chain = prompt | chat

response = chain.invoke({"question": "What is the difference between RAG and fine-tuning?"})
print(response.content)
# → "RAG retrieves external context at inference time; fine-tuning bakes knowledge into model weights."
```

**Parameters:**
```python
get_chat_llm(
    model: Optional[str] = None,       # Overrides OLLAMA_MODEL from .env
    temperature: float = 0.7,          # Creativity level (0.0-1.0)
    format: Optional[str] = None,      # "json" for structured output
    num_ctx: Optional[int] = None,     # Context window size (default: model-specific)
    **kwargs                           # Any additional ChatOllama parameters
)
```

**JSON Mode Example:**

```python
chat = get_chat_llm(format="json")
result = chat.invoke("Return a JSON with keys 'name' and 'age' for a person named Alice who is 30")
# → '{"name": "Alice", "age": 30}'
```

**Extended Context Window Example:**

```python
# For processing long documents
chat = get_chat_llm(num_ctx=8192)  # 8K token context window
```

---

### `get_embeddings()` — Semantic Search & RAG

Returns dense vector representations of text for use with any LangChain vector store.

**Use Cases:**
- Retrieval-Augmented Generation (RAG)
- Semantic search
- Document similarity
- Vector store operations

**Example:**

```python
from common.llm_factory import get_embeddings
from langchain_core.vectorstores import InMemoryVectorStore

embeddings = get_embeddings()  # uses OLLAMA_EMBEDDING_MODEL from .env; add model= to override

docs = [
    "LangChain simplifies building LLM applications.",
    "Ollama lets you run large language models locally.",
    "RAG combines retrieval with language model generation.",
]
vector_store = InMemoryVectorStore.from_texts(docs, embedding=embeddings)

results = vector_store.similarity_search("How do I run LLMs on my machine?", k=1)
print(results[0].page_content)
# → "Ollama lets you run large language models locally."
```

**Parameters:**
```python
get_embeddings(
    model: Optional[str] = None,       # Overrides OLLAMA_EMBEDDING_MODEL from .env
    **kwargs                           # Any additional OllamaEmbeddings parameters
)
```

---

## Advanced Usage

### Override Model Per Call

```python
# Use default model (from .env)
llm_default = get_llm()

# Use specific model for this instance
llm_large = get_llm(model="llama3.1:8b")
llm_small = get_llm(model="gemma2:2b")
```

### Chain Composition with LCEL

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | get_chat_llm(temperature=0.3) | StrOutputParser()
result = chain.invoke({"question": "..."})
```

### Agent with Tools

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def search_tool(query: str) -> str:
    """Search the web for information."""
    return "Search results..."

agent = create_react_agent(
    model=get_chat_llm(),
    tools=[search_tool]
)
```

### Credential Management

The LLM Factory automatically retrieves `OLLAMA_API_KEY` using the following strategy:

1. **HashiCorp Vault** (if enabled via `VAULT_ENABLED=true` in `.env`)
2. **Environment variable** (`.env` file fallback)

For details on HashiCorp Vault integration, see [vault.md](vault.md).

---

## See Also

- [Models Guide](models.md) — Full model reference and performance comparison
- [HashiCorp Vault](vault.md) — Centralized secret management
- [Getting Started](getting_started.md) — Environment setup
