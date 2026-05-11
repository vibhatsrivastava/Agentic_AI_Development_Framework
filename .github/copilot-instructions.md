# GitHub Copilot Workspace Instructions

> Applies to all files in this repository.

---

## Repo Overview

This is a **Python monorepo** of Agentic AI projects built with [LangChain](https://docs.langchain.com/) and [LangGraph](https://langchain-ai.github.io/langgraph/), running LLMs via [Ollama](https://ollama.com/) (local or remote hosted).

**Current branch:** `dev` | **Default branch:** `main`

---

## Repository Structure

```
Agentic_AI_Development_Framework/
├── common/                    # Shared utilities — import from any project
│   ├── llm_factory.py         # LLM builders: get_llm(), get_chat_llm(), get_embeddings()
│   ├── utils.py               # get_logger(), require_env()
│   └── prompts/
│       └── base_prompts.py    # QA_PROMPT, RAG_PROMPT, REACT_SYSTEM_PROMPT
├── projects/                  # Self-contained AI projects
│   └── 01_hello_langchain/    # Minimal LCEL chain example
├── planner/                   # Practice use case documents (.md) and scripts
├── Quick-Reference/           # Concept guides for learning and interview prep
├── docs/                      # Setup and contribution documentation
├── .env.example               # Required environment variable template
└── requirements-base.txt      # Shared base dependencies for all projects
```

---

## Environment Setup

**Each project has its own isolated `.venv`, created automatically by the CLI when scaffolding.**

```powershell
# Install uv once (replaces pip + pipx)
pip install uv
# Or the standalone installer (no Python required):
# Windows: powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install the AI Agent Builder CLI globally (isolated, no venv needed)
uv tool install ./cli

# Scaffold a new project — venv is created automatically
ai-agent-builder new-project 03_my_agent

# Activate the project venv and start working
cd projects/03_my_agent
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # Mac/Linux
```

**For the root-level test suite only** (running `pytest` from repo root across all projects):

```powershell
# Create a root dev venv with test tooling + common
uv venv .venv
uv pip install -e ./common
uv pip install -r requirements-base.txt
```

**Required `.env` variables** (copy from `.env.example`):

**Root `.env` (Common/Shared Variables)**:

| Variable | Purpose | Example |
|---|---|---|
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` or remote URL |
| `OLLAMA_API_KEY` | Bearer token for remote servers; blank for local | `your_token` |
| `OLLAMA_MODEL` | Default LLM model | `gpt-oss:20b` |
| `OLLAMA_EMBEDDING_MODEL` | Default embedding model | `nomic-embed-text` |
| `LOG_LEVEL` | Logging verbosity | `INFO` |

**Hierarchical Environment Loading Strategy:**

This repository uses a **two-tier environment system** to keep the root `.env` clean and scalable:

1. **Root `.env`** → Common/shared variables (OLLAMA_*, VAULT_*, LOG_LEVEL)
2. **Project `.env`** (optional) → Integration-specific variables (GITHUB_*, REDIS_*, PGVECTOR_*, etc.)

**How it works:**
- `load_project_env()` from `common.utils` loads **both** root `.env` and project `.env` (if exists)
- Simple projects (e.g., 01_hello_langchain) use only root `.env` — no project `.env` needed
- Integration projects (e.g., 04_github_issue_reporter) add a project `.env` for integration variables
- Project values override root values (allows per-project customization)

**Example:**
```
Agentic_AI_Development_Framework/
├── .env                           # Common: OLLAMA_*, VAULT_*, LOG_LEVEL
├── projects/
│   ├── 01_hello_langchain/        # ✅ No project .env (uses root .env only)
│   └── 04_github_issue_reporter/
│       ├── .env                   # ✅ GitHub-specific: GITHUB_TOKEN, etc.
│       └── .env.example           # Template for project .env
```

**Benefits:**
- ✅ Root `.env` stays clean as projects grow
- ✅ Only configure tokens for integrations you actually use
- ✅ Clear separation: common variables vs. integration variables
- ✅ Backward compatible: existing projects continue to work

**Optional: HashiCorp Vault Integration**

For teams with multiple developers, use **HashiCorp Vault** for centralized secret management:

| Variable | Purpose | Example |
|---|---|---|
| `VAULT_ENABLED` | Enable Vault (default: `false`) | `true` |
| `VAULT_ADDR` | Vault server URL | `http://vault.example.com:8200` |
| `VAULT_TOKEN` | Vault authentication token | `hvs.your_vault_token` |
| `VAULT_SECRET_PATH` | Secret path (default: `ollama`) | `ollama` |
| `VAULT_MOUNT_POINT` | KV mount point (default: `secret`) | `secret` |

When `VAULT_ENABLED=true`, `OLLAMA_API_KEY` is retrieved from Vault with automatic fallback to `.env` if unreachable. See [docs/vault.md](../docs/vault.md) for setup instructions.

**Credential Retrieval Strategy:**
- `common/llm_factory.py` uses `common/vault.py::get_secret()` for API key retrieval
- **Vault-first**: Tries Vault if enabled; logs success/failure
- **Automatic fallback**: Uses `.env` if Vault unreachable or key not found
- **Zero code changes**: Projects use `get_llm()` as before — credential source is transparent
- **Backward compatible**: Vault disabled by default; existing workflows unchanged

**Optional: Langfuse Observability (Always-On by Default)**

Automatic LLM tracing, cost tracking, and performance analytics via **Langfuse**. All LLM calls are traced automatically via `common/llm_factory` — **no code changes needed**.

| Variable | Purpose | Example |
|---|---|---|
| `LANGFUSE_ENABLED` | Enable/disable tracing (default: `true`) | `true` |
| `LANGFUSE_PUBLIC_KEY` | Public API key from Langfuse dashboard | `pk-lf-...` |
| `LANGFUSE_SECRET_KEY` | Secret API key from Langfuse dashboard | `sk-lf-...` |
| `LANGFUSE_HOST` | Langfuse server URL (cloud or self-hosted) | `http://10.0.0.15:3000` |

**How it works:**
- Tracing is **always-on by default** — set `LANGFUSE_ENABLED=false` to disable globally
- Callbacks are automatically attached to all LLM instances (`get_llm()`, `get_chat_llm()`, `get_embeddings()`)
- Supports Vault integration: keys fetched from Vault path "langfuse" with `.env` fallback
- Graceful degradation: LLMs work normally if Langfuse unavailable or keys missing
- Zero code changes: existing projects automatically get tracing after configuring `.env`

**Quick setup:**
1. Create project at your Langfuse instance (e.g., http://10.0.0.15:3000)
2. Generate API keys (Settings → API Keys)
3. Add keys to root `.env` or Vault
4. Run any project → traces appear in Langfuse dashboard automatically

See [docs/langfuse.md](../docs/langfuse.md) for detailed setup instructions, dashboard walkthrough, and troubleshooting.

---

## The `common/` Package — Always Use It

Every project **must** use the shared `common/` package instead of directly instantiating LangChain classes. The `common/` package is installed as an editable package (`ai-agent-common`) into each project's `.venv` by the CLI scaffold. No `sys.path` manipulation is needed:

```python
# Direct import — works because ai-agent-common is installed in the project venv
from common.llm_factory import get_llm, get_chat_llm, get_embeddings
from common.utils import get_logger
```

### LLM Factory — Which Builder to Use

| Builder | Returns | Use When |
|---|---|---|
| `get_llm()` | `OllamaLLM` | Simple string chains, single-turn prompts, no message history |
| `get_chat_llm()` | `ChatOllama` | Agents, memory, tool-calling, JSON mode, LangGraph nodes |
| `get_embeddings()` | `OllamaEmbeddings` | RAG, vector stores, similarity search |

```python
from common.llm_factory import get_llm, get_chat_llm, get_embeddings

llm        = get_llm()                                     # OllamaLLM, default model
chat       = get_chat_llm()                                # ChatOllama, default model
chat_json  = get_chat_llm(format="json")                   # structured output
chat_large = get_chat_llm(model="llama3.1:8b", num_ctx=8192)
embeddings = get_embeddings()                              # nomic-embed-text
```

All builders read `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, and `OLLAMA_MODEL` from `.env`. The `model=` argument overrides the env default for that call only.

### Shared Utilities

```python
from common.utils import get_logger, require_env

logger   = get_logger(__name__)          # structured logger; reads LOG_LEVEL from .env
base_url = require_env("OLLAMA_BASE_URL") # raises EnvironmentError if key is missing
```

### Shared Prompts

```python
from common.prompts.base_prompts import QA_PROMPT, RAG_PROMPT, REACT_SYSTEM_PROMPT
```

---

## Coding Conventions

### Chain Composition — Always Use LCEL

Use the `|` pipe operator (LangChain Expression Language) to compose chains:

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | get_llm() | StrOutputParser()
result = chain.invoke({"question": "..."})
```

### Agents — Prefer LangGraph

For new agents, use `langgraph.prebuilt.create_react_agent` over `AgentExecutor`:

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool

@tool
def my_tool(input: str) -> str:
    """Tool description the LLM uses to decide when to call it."""
    return ...

agent = create_react_agent(model=get_chat_llm(), tools=[my_tool])
result = agent.invoke({"messages": [{"role": "user", "content": "..."}]})
answer = result["messages"][-1].content
```

### Tool Definitions

- Decorate with `@tool` from `langchain_core.tools`
- Write a clear, specific docstring — the LLM reads it to decide when to call the tool
- Use typed parameters; avoid `**kwargs`
- Return a `str` for simple tools; use Pydantic schemas for complex inputs

### Project Structure for New Projects

```
projects/NN_project_name/
├── .venv/             # Per-project isolated venv (created by CLI, gitignored)
├── .env               # Optional: Integration-specific variables (gitignored)
├── .env.example       # Optional: Template for project .env (committed)
├── src/
│   └── main.py            # Entry point; uses common/ imports
├── requirements.txt       # Project-specific deps only
└── README.md              # Description, usage, sample output
```

**Environment Variable Guidelines:**

- **Simple projects** (no integrations): No project `.env` or `.env.example` needed. Use root `.env` only.
- **Integration projects** (GitHub, Redis, etc.): Create project `.env.example` as template, copy to `.env` for configuration.
- **Common variables** (OLLAMA_*, VAULT_*, LOG_LEVEL): Always live in root `.env` only.
- **Integration variables** (GITHUB_*, REDIS_*, PGVECTOR_*): Live in project `.env`.
- All projects must use `load_project_env()` from `common.utils` to enable hierarchical loading.

---

## Documentation Conventions

### Quick-Reference

Files in `Quick-Reference/` follow indexed naming (`01_`, `02_`, ...) and cover concepts with definitions, diagrams, examples, and interview Q&A. See existing files for format reference.

### Planner

Files in `planner/` are practice use cases. Each `.md` file documents one scenario with sections: Use Case Description, Objective, Step-by-Step Thought Process, Pseudo Code, High Level Workflow Diagram, Low Level Workflow Diagram, Implementation Steps, Code Snippets, Test Cases, Expected Outcomes.

A corresponding `.py` file contains the runnable implementation.

---

## Testing Conventions

**All code must maintain >= 75% test coverage.** This repository uses a pragmatic testing approach optimized for AI agent development. See [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) for the complete philosophy.

### Testing Framework

- **Framework**: pytest >=8.0.0 with pytest-cov, pytest-mock, pytest-asyncio
- **Coverage threshold**: 75% minimum (enforced via `pytest.ini`)
- **Mock strategy**: All LLM/Ollama calls must be mocked (no real API calls in tests)
- **Manual validation**: Test with real Ollama before PR merge

### Running Tests

```powershell
# Run all tests with coverage report
pytest --cov --cov-report=term-missing

# Run tests for specific module
pytest common/tests/test_llm_factory.py -v

# Verify >= 75% coverage (fails if below threshold)
pytest --cov --cov-fail-under=75

# Run only unit tests (fast)
pytest -m unit

# Skip integration tests (CI mode)
pytest -m "not integration"
```

### Test Structure

Each project/module has a `tests/` directory parallel to the code:

```
common/
├── llm_factory.py
└── tests/
    ├── conftest.py             # Shared fixtures (mock_llm, mock_chat_llm)
    ├── test_llm_factory.py     # Tests for llm_factory.py
    └── test_utils.py           # Tests for utils.py

projects/01_hello_langchain/
├── src/
│   └── main.py
└── tests/
    ├── conftest.py             # Project-specific fixtures
    └── test_main.py            # Tests for main.py
```

### Critical Rules

1. **Mock all LLMs**: Never make real Ollama/LLM API calls in tests. Use `mock_llm`, `mock_chat_llm`, and `mock_embeddings` fixtures from `common/tests/conftest.py`
2. **75% coverage minimum**: Every new module must achieve >= 75% coverage
3. **Test before commit**: Always run `pytest --cov --cov-fail-under=75` before pushing code
4. **Manual validation required**: Test with real Ollama before PR merge
5. **Test types required**: Unit tests (isolated functions), Integration tests (mocked chains/agents), Manual smoke tests (real LLM)

### Documentation

- **Detailed testing guide**: [docs/testing.md](docs/testing.md) — Comprehensive patterns and examples
- **Testing strategy**: [docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md) — Philosophy and approach
- **Configuration**: `pytest.ini` — Coverage thresholds and test discovery

**Remember**: No code is complete without tests. Coverage is non-negotiable.

---

## Running Projects

```powershell
# Activate the project venv, then run
cd projects/01_hello_langchain
.venv\Scripts\Activate.ps1
python src/main.py
```

---

## Key Documentation

- [docs/getting_started.md](docs/getting_started.md) — Full environment setup
- [docs/models.md](docs/models.md) — Model reference, LLM class guide, how to swap models
- [docs/contributing.md](docs/contributing.md) — How to add a new project
- [docs/prerequisites.md](docs/prerequisites.md) — System requirements
- [Quick-Reference/01_What_Is_Agentic_AI.md](Quick-Reference/01_What_Is_Agentic_AI.md) — Concepts overview
- [Quick-Reference/02_ReAct_Pattern_Deep_Dive.md](Quick-Reference/02_ReAct_Pattern_Deep_Dive.md) — ReAct pattern
- [Quick-Reference/03_RAG_Retrieval_Augmented_Generation.md](Quick-Reference/03_RAG_Retrieval_Augmented_Generation.md) — RAG pipeline
- [Quick-Reference/04_Ollama.md](Quick-Reference/04_Ollama.md) — Ollama setup and API

---

## Common Pitfalls

- **`common/` import errors** — The project venv must have `ai-agent-common` installed. Run `uv pip install -e ./common` from the repo root targeting the project venv, or re-scaffold using `ai-agent-builder new-project`
- **Do NOT add `sys.path.insert`** — `common/` is a proper installable package; path hacks are no longer needed or used
- **`.env` not found** — `llm_factory.py` calls `load_project_env()` which searches upward; ensure `.env` exists at repo root
- **PR tests failing with ImportError** — The CI workflow installs all project `requirements.txt` files via a loop. If you added a new import, ensure it's listed in your project's `requirements.txt`. For dependencies used by 3+ projects, add to root `requirements-base.txt`. See [Testing Strategy](../docs/TESTING_STRATEGY.md#dependency-management-in-ci) for details.
- **Project `.env` usage** — Integration-specific projects (GitHub, Redis, etc.) MAY have a project `.env` file for integration variables only. Common variables (OLLAMA_*, VAULT_*) always live in root `.env`. Simple projects use only root `.env`. Projects automatically load both via `load_project_env()` from `common.utils`.
- **Wrong LLM class** — Use `get_chat_llm()` (not `get_llm()`) for agents and LangGraph nodes; `OllamaLLM` does not support tool calling
- **Model not available** — Run `ollama list` to see downloaded models; run `ollama pull <model>` if missing
- **`OLLAMA_API_KEY` left blank for remote** — Remote Ollama servers require the Bearer token; check `.env`
- **`venv/` vs `.venv/`** — Each project uses `.venv/` inside its own directory; the root `.venv/` is only for repo-wide test runs
- **Langfuse not tracing** — Check logs for "Successfully initialized Langfuse callback handler" message. Common issues:
  - `LANGFUSE_ENABLED=false` in `.env` (tracing disabled)
  - Missing `LANGFUSE_PUBLIC_KEY` or `LANGFUSE_SECRET_KEY` in `.env` or Vault
  - `LANGFUSE_HOST` unreachable (check URL and network connectivity)
  - `langfuse` library not installed (run `uv pip install -e ./common` to install dependencies)
- **Langfuse traces not appearing** — Verify API keys are correct (check Langfuse dashboard Settings → API Keys), ensure project exists in Langfuse, check Langfuse server is running
