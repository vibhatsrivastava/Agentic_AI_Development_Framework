# Agentic AI Development Framework

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![LangChain](https://img.shields.io/badge/LangChain-latest-green?logo=chainlink)
![Ollama](https://img.shields.io/badge/Ollama-local%20%7C%20hosted-orange)
![Tests](https://img.shields.io/github/actions/workflow/status/vibhatsrivastava/Agentic_AI_Development_Framework/test.yml?label=tests)
![License](https://img.shields.io/github/license/vibhatsrivastava/Agentic_AI_Development_Framework)

A curated **monorepo** of Agentic AI applications built with [LangChain](https://docs.langchain.com/) and [Ollama](https://ollama.com/). Each project is self-contained and demonstrates a specific use case, integration, or agentic pattern.

> **TL;DR**: Production-ready LangChain projects with SDK tooling, shared utilities, 90% test coverage, and optional Vault integration. Get from zero to running agent in <5 minutes.

---

## What You Get

### 🎯 Technology Stack

| Component | Technology |
|-----------|-----------|
| **LLM Framework** | [LangChain](https://docs.langchain.com/) + [LangGraph](https://langchain-ai.github.io/langgraph/) |
| **LLM Runtime** | [Ollama](https://ollama.com/) (remote hosted or local) |
| **Default Model** | `gpt-oss:20b` (20B parameter OSS model) |
| **Embeddings** | `nomic-embed-text` via Ollama |
| **Secret Management** | [HashiCorp Vault](https://www.vaultproject.io/) (optional) |
| **Testing** | pytest with 75% coverage requirement |

### ⚡ Key Features

- **🚀 SDK Scaffolding** — Generate production-ready projects in <2 minutes with `ai-agent-builder` CLI
- **🏭 Shared Architecture** — Reusable LLM factory, prompts, utilities across all projects
- **🔌 Composable Integrations** — Mix-and-match vector stores (pgvector, Chroma, FAISS), caching (Redis), observability (Langfuse), orchestration (Ansible AWX)
- **🧪 Built-in Testing** — Pre-configured pytest fixtures, mocked LLMs, 90% coverage templates
- **🔐 Enterprise-Ready** — Optional Vault integration, rate limiting, retry logic, token counting
- **📚 Learning Resources** — Quick-reference guides for Agentic AI, ReAct patterns, RAG pipelines

---

## Available Projects

| # | Project | Type | Description |
|---|---------|------|-------------|
| 01 | [Hello LangChain](projects/01_hello_langchain/) | LCEL | Minimal working example — chain setup, LLM call, prompt template |

> **More projects coming soon!** Use the SDK to create your own: `ai-agent-builder new-project 02_my_agent --arch langgraph`

---

## 🚀 Quick Start

> **Prerequisites**: Ensure you have [Python 3.10+, Ollama access, and Git](docs/prerequisites.md) installed.

```powershell
# 1. Install uv (run once — replaces pip + venv)
# Windows (standalone, no Python required):
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
# macOS/Linux:
# curl -LsSf https://astral.sh/uv/install.sh | sh
# Or via pip if Python is already installed:
# pip install uv

# 2. Clone and navigate to repo
git clone https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework.git
cd Agentic_AI_Development_Framework

# 3. Set up environment
cp .env.example .env
# Edit .env with your OLLAMA_BASE_URL and OLLAMA_API_KEY

# 4. Install the CLI (isolated — no venv needed)
uv tool install ./cli

# 5. Scaffold a new project
# The CLI automatically creates a .venv, installs requirements-base.txt and common
ai-agent-builder new-project 02_my_rag_app --arch lcel --integrations pgvector,langfuse

# 6. Run your project
cd projects/02_my_rag_app
.venv\Scripts\Activate.ps1   # Windows
# source .venv/bin/activate  # macOS/Linux
python src/main.py
```

**What the CLI does automatically when scaffolding a project:**
- ✅ Creates an isolated `.venv` inside the project directory
- ✅ Installs `requirements-base.txt` (shared base dependencies)
- ✅ Installs `common/` as an editable package (`ai-agent-common`)
- ✅ Generates LCEL/LangGraph/Custom architecture from templates
- ✅ Generates integration code (pgvector, Redis, Langfuse, Chroma, FAISS, AWX)
- ✅ Generates test fixtures with 90% coverage template
- ✅ Generates `.env.example` with all required variables
- ✅ Generates README with setup instructions

**Benefits**: 15 minutes → <2 minutes per project | Zero boilerplate | Composable integrations

> See **[docs/sdk.md](docs/sdk.md)** for complete SDK documentation, integration catalog, and advanced usage.

---

## 📁 How It Works

### Repository Structure

```
Agentic_AI_Development_Framework/
├── cli/                       # 🚀 SDK for project scaffolding
│   ├── ai_agent_builder/         # CLI implementation
│   └── templates/             # LCEL/LangGraph/Custom templates
├── projects/                  # 📦 Individual AI projects (self-contained)
│   └── 01_hello_langchain/    # Example: minimal LCEL chain
├── common/                    # 🏭 Shared utilities (import from any project)
│   ├── llm_factory.py         # LLM builders: get_llm(), get_chat_llm(), get_embeddings()
│   ├── vault.py               # Optional Vault integration for secret management
│   ├── utils.py               # Logging, env helpers (get_logger, require_env)
│   ├── retry.py               # Retry logic with exponential backoff
│   ├── rate_limiter.py        # Rate limiting for API calls
│   ├── token_counter.py       # Token usage tracking
│   └── prompts/               # Shared prompt templates (QA, RAG, ReAct)
├── docs/                      # 📚 Comprehensive documentation
├── Quick-Reference/           # 🎓 Learning resources (Agentic AI, ReAct, RAG, Ollama)
├── planner/                   # 🧪 Practice scenarios and implementations
├── .env.example               # Environment variable template (copy to .env)
├── requirements-base.txt      # Shared base dependencies
└── pytest.ini                 # Test configuration (90% coverage threshold)
```

---

### Core Architecture

#### 🏭 Common LLM Factory

**All projects use the shared `common/llm_factory.py`** for consistent LLM access. Never instantiate LangChain classes directly.

```python
from common.llm_factory import get_llm, get_chat_llm, get_embeddings

# Simple string chains, single-turn prompts
llm = get_llm()  

# Agents, memory, tool-calling, JSON mode, LangGraph nodes
chat = get_chat_llm(format="json", model="llama3.1:8b")  

# RAG, vector stores, similarity search
embeddings = get_embeddings()  
```

**Why use it?**
- ✅ Automatic `.env` configuration (reads `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, `OLLAMA_MODEL`)
- ✅ Optional Vault integration (automatic fallback to `.env`)
- ✅ Consistent error handling across projects
- ✅ Easy model swapping without code changes

> See [docs/llm_factory.md](docs/llm_factory.md) for detailed usage guide and examples.

---

#### 🔐 HashiCorp Vault Integration (Optional)

**Enterprise secret management** for teams. Store `OLLAMA_API_KEY` centrally instead of in individual `.env` files.

**Key Benefits:**
- **Centralized management**: One secret accessible to all developers
- **Automatic fallback**: Seamlessly falls back to `.env` if Vault unreachable
- **Zero code changes**: Projects use `get_llm()` as before — transparent credential retrieval
- **Audit trail**: Track who accessed secrets and when

**Quick Setup:**
```bash
# Enable in .env
VAULT_ENABLED=true
VAULT_ADDR=http://vault.example.com:8200
VAULT_TOKEN=hvs.your_vault_token
```

> Vault is **disabled by default**. See [docs/vault.md](docs/vault.md) for complete setup.

---

#### 🧪 Testing Philosophy

**All code must maintain ≥90% test coverage** (enforced via `pytest.ini`).

```powershell
# Run tests with coverage report
pytest --cov --cov-report=term-missing

# Verify ≥90% coverage (fails if below threshold)
pytest --cov --cov-fail-under=90
```

**Testing conventions:**
- All LLM/Ollama calls **must be mocked** (no real API calls in tests)
- Use shared fixtures from `common/tests/conftest.py` (`mock_llm`, `mock_chat_llm`, `mock_embeddings`)
- SDK auto-generates test templates with 90% coverage baseline

> See [docs/testing.md](docs/testing.md) for comprehensive testing guide and patterns.

---

### Project Scaffold

Each project under `projects/` follows this standard structure:

```
projects/NN_project_name/
├── src/
│   └── main.py            # Entry point (uses common/ imports)
├── tests/
│   ├── conftest.py        # Project-specific fixtures
│   └── test_main.py       # ≥90% coverage tests
├── requirements.txt       # Project-specific deps (delta on base)
└── README.md              # Description, usage, sample output
```

> **Never create project-level `.env` files.** All environment variables belong in root `.env.example` and are documented in project README if project-specific.

---

## 🔄 CI/CD Pipeline

**Automated implementation and deployment** powered by GitHub Actions with CODEOWNERS approval workflow.

### Key Features

- 🤖 **Auto-Implementation**: CODEOWNERS approve issues with `/implement-plan` or `/approved` commands
- 🔐 **Manual Production Approval**: Deployment to `main` requires CODEOWNER approval
- 🌿 **Branch & Model Configuration**: Specify custom branch and LLM model for each implementation
- 📋 **Context-Aware**: Collects all issue comments and feedback before implementation
- 🚀 **Automated Staging**: Deploy to staging automatically from `dev` branch
- 📢 **Teams Notifications**: Rich adaptive card notifications in Microsoft Teams for PR events

### Quick Commands

```bash
# Trigger implementation (in issue comment, CODEOWNERS only)
/implement-plan                                    # Uses defaults
/implement-plan branch=feature/auth model=llama3.1:8b  # Custom config
/approved branch=hotfix/security-fix               # Alternative command
```

### Documentation

| Guide | Description |
|-------|-------------|
| **[CI/CD Overview](docs/ci-cd.md)** | Complete pipeline documentation, workflows, security |
| **[Quick Reference](docs/ci-cd-quickref.md)** | Quick commands, troubleshooting, common tasks |
| **[Teams Notifications](docs/teams-notifications.md)** | Microsoft Teams PR notifications setup and configuration |

---

## 📚 Documentation

| Guide | Description | Best For |
|-------|-------------|----------|
| **[Getting Started](docs/getting_started.md)** | Environment setup, local vs. hosted Ollama, troubleshooting | First-time setup, Ollama configuration |
| **[Developer SDK](docs/sdk.md)** | CLI documentation, integration catalog, advanced scaffolding | Creating new projects, using integrations |
| **[LLM Factory](docs/llm_factory.md)** | `get_llm()` vs `get_chat_llm()` guide, model swapping, usage patterns | Choosing the right LLM builder, debugging |
| **[Models](docs/models.md)** | Model reference, alternatives, swapping guide, class comparison | Switching models, understanding capabilities |
| **[Testing](docs/testing.md)** | Testing conventions, mocking patterns, coverage requirements | Writing tests, achieving 90% coverage |
| **[HashiCorp Vault](docs/vault.md)** | Vault setup, configuration, team workflows | Enterprise deployments, secret management |
| **[CI/CD Pipeline](docs/ci-cd.md)** | Automated workflows, CODEOWNERS approval, deployment | Setting up automation, approving implementations |
| **[Contributing](docs/contributing.md)** | Project naming, scaffold requirements, conventions | Adding new projects, following standards |
| **[Prerequisites](docs/prerequisites.md)** | System requirements, installation guides | Initial setup, dependency installation |

### 🎓 Learning Resources

| Resource | Topic |
|----------|-------|
| [Quick-Reference/01_What_Is_Agentic_AI.md](Quick-Reference/01_What_Is_Agentic_AI.md) | Agentic AI concepts, definitions, patterns |
| [Quick-Reference/02_ReAct_Pattern_Deep_Dive.md](Quick-Reference/02_ReAct_Pattern_Deep_Dive.md) | Reason + Act pattern, implementation guide |
| [Quick-Reference/03_RAG_Retrieval_Augmented_Generation.md](Quick-Reference/03_RAG_Retrieval_Augmented_Generation.md) | RAG pipeline, vector stores, embeddings |
| [Quick-Reference/04_Ollama.md](Quick-Reference/04_Ollama.md) | Ollama setup, API reference, model management |

---

## 🤝 Contributing

We welcome contributions! To add a new project:

1. **Use the SDK** (recommended): `ai-agent-builder new-project NN_your_project --arch [lcel|langgraph|custom]`
2. **Follow naming convention**: `NN_descriptive_name` (e.g., `02_pdf_qa_agent`)
3. **Include tests**: Achieve ≥90% coverage (`pytest --cov --cov-fail-under=90`)
4. **Update this README**: Add your project to the [Available Projects](#available-projects) table
5. **Document thoroughly**: Write a comprehensive README in your project directory

See [docs/contributing.md](docs/contributing.md) for complete guidelines.

---

## 📄 License

[MIT](LICENSE) — Free to use, modify, and distribute.
