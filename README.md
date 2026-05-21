# Agentic AI Development Framework

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![LangChain](https://img.shields.io/badge/LangChain-latest-green?logo=chainlink)
![Ollama](https://img.shields.io/badge/Ollama-local%20%7C%20hosted-orange)
![Tests](https://img.shields.io/github/actions/workflow/status/vibhatsrivastava/Agentic_AI_Development_Framework/test.yml?label=tests)
![License](https://img.shields.io/github/license/vibhatsrivastava/Agentic_AI_Development_Framework)

A production-ready **monorepo** for building Agentic AI applications with [LangChain](https://docs.langchain.com/) and [Ollama](https://ollama.com/). Get from zero to running agent in under 5 minutes with built-in scaffolding, shared utilities, and enterprise-grade features.

> **TL;DR**: Production LLM projects with SDK tooling, automatic observability, 75% test coverage, and optional Vault integration. Perfect for teams building multiple AI agents with consistent patterns.

---

## Quick Start

**Prerequisites**: [Python 3.10+, Ollama, Git](docs/prerequisites.md)

```powershell
# 1. Install uv package manager
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# 2. Clone repository
git clone https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework.git
cd Agentic_AI_Development_Framework

# 3. Configure environment
cp .env.example .env
# Edit .env with your OLLAMA_BASE_URL and other settings

# 4. Install CLI globally
uv tool install ./cli

# 5. Create your first project (auto-creates venv and installs dependencies)
ai-agent-builder new-project 02_my_agent --arch langgraph

# 6. Run your agent
cd projects/02_my_agent
.venv\Scripts\Activate.ps1   # Windows
python src/main.py
```

**What just happened?** The CLI automatically created a `.venv`, installed all dependencies, generated a complete LangGraph agent with tests, and configured observability. You're ready to code.

---

## Core Features

### 🎯 **What You Get Out of the Box**

Every project created with this framework includes:

#### **Foundation (Always Available)**
- **LLM Factory** — Unified interface (`get_llm()`, `get_chat_llm()`, `get_embeddings()`) for Ollama models
- **HashiCorp Vault Integration** — Optional centralized secret management with `.env` fallback
- **Langfuse Observability** — Always-on LLM tracing, cost tracking, and performance analytics (can be disabled)
- **Rate Limiting** — Token bucket algorithm prevents API rate limit issues
- **Retry Logic** — Exponential backoff for transient failures
- **Token Counting** — Track LLM usage and estimate costs
- **Structured Logging** — Configurable logging with `LOG_LEVEL` support
- **Environment Management** — Hierarchical `.env` loading (root + project-specific)

#### **SDK Scaffolding (`ai-agent-builder` CLI)**
- **3 Architecture Templates** — LCEL chains, LangGraph agents, or custom minimal projects
- **Automatic Setup** — Creates `.venv`, installs dependencies, generates tests with 75% coverage baseline
- **Integration Code Generation** — Mix-and-match vector stores, caching, and monitoring
- **Project Validation** — Built-in checks for structure and configuration correctness

#### **Enterprise Ready**
- **CI/CD Pipeline** — GitHub Actions with automated testing, CODEOWNERS approval, staging/production deployment
- **GitHub Copilot Integration** — Assign issues to Copilot with `/implement-plan` command
- **Microsoft Teams Notifications** — Rich adaptive cards for PR events and issue updates
- **Multi-Repository Support** — Manage multiple projects with flexible token management

---

## Available Integrations

### **Vector Stores (RAG)**
| Integration | Type | Use Case |
|---|---|---|
| **Chroma** | Local | Development and prototyping |
| **pgvector** | PostgreSQL | Production RAG systems |
| **FAISS** | Local | High-performance CPU-optimized search |

### **Caching**
| Integration | Type | Use Case |
|---|---|---|
| **Redis** | In-memory | Cache expensive LLM calls, session storage |
| **In-Memory LRU** | Built-in | Simple projects without Redis |

### **Observability**
| Integration | Type | Use Case |
|---|---|---|
| **Langfuse** | Always-on | LLM tracing, cost tracking, evals |

### **Automation & Orchestration**
| Integration | Type | Use Case |
|---|---|---|
| **Ansible AWX** | Orchestration | Scheduled agent execution, credential management |
| **GitHub Actions** | CI/CD | Automated testing, deployment, Copilot integration |

### **Platform Integrations**
| Integration | Type | Use Case |
|---|---|---|
| **GitHub API** | Platform | Issue reporting, analysis, automated recommendations |
| **Microsoft Teams** | Notifications | Adaptive cards for reports and alerts |

**Generate projects with integrations:**
```powershell
# RAG system with pgvector and Langfuse
ai-agent-builder new-project 03_rag_app --arch lcel --integrations pgvector,langfuse

# Cached agent with Redis
ai-agent-builder new-project 04_cached_agent --arch langgraph --integrations redis
```

See **[docs/sdk.md](docs/sdk.md)** for complete integration catalog and usage guide.

---

## Repository Structure

```
Agentic_AI_Development_Framework/
├── cli/                       # SDK for project scaffolding (ai-agent-builder)
├── common/                    # Shared utilities (imported by all projects)
│   ├── llm_factory.py         # get_llm(), get_chat_llm(), get_embeddings()
│   ├── langfuse_tracing.py    # Always-on observability callbacks
│   ├── vault.py               # Optional Vault integration
│   ├── rate_limiter.py        # Token bucket rate limiting
│   ├── retry.py               # Exponential backoff retry logic
│   ├── token_counter.py       # Usage tracking
│   ├── utils.py               # get_logger(), require_env(), load_project_env()
│   └── prompts/               # Shared prompt templates (QA, RAG, ReAct)
├── projects/                  # Self-contained AI projects
│   ├── 01_hello_langchain/    # Minimal LCEL chain example
│   ├── 03_weather_reporting_agent/  # LangGraph agent with tools
│   └── 04_github_issue_reporter/    # GitHub API integration, AWX automation
├── docs/                      # Comprehensive documentation
├── Quick-Reference/           # Learning resources (concepts, patterns)
├── .env.example               # Environment template (copy to .env)
├── requirements-base.txt      # Shared dependencies
└── pytest.ini                 # Test configuration (75% coverage)
```

**Architecture principle**: `common/` package provides shared infrastructure. Projects import from `common/` as an installed package (`ai-agent-common`), never using path hacks.

---

## Example Projects

| # | Project | Architecture | Integrations | Description |
|---|---------|--------------|--------------|-------------|
| 01 | [Hello LangChain](projects/01_hello_langchain/) | LCEL | None | Minimal chain: prompt → LLM → parser |
| 03 | [Weather Agent](projects/03_weather_reporting_agent/) | LangGraph | None | ReAct agent with custom tools |
| 04 | [GitHub Issue Reporter](projects/04_github_issue_reporter/) | LangGraph | GitHub API, AWX, Teams | Automated issue analysis, Teams notifications |

Create your own:
```powershell
ai-agent-builder new-project 05_my_project --arch [lcel|langgraph|custom]
```

---

## How It Works

### 1. **Shared LLM Factory** (Always Use This)

All projects use `common/llm_factory.py` for consistent LLM access:

```python
from common.llm_factory import get_llm, get_chat_llm, get_embeddings

# Simple string chains, single-turn prompts
llm = get_llm()

# Agents, memory, tool-calling, JSON mode, LangGraph
chat = get_chat_llm(format="json")

# RAG, vector stores, similarity search
embeddings = get_embeddings()
```

**Benefits:**
- Automatic `.env` configuration (reads `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, `OLLAMA_MODEL`)
- Optional Vault integration with automatic fallback
- Always-on Langfuse tracing (can be disabled)
- Easy model swapping via environment variables

See **[docs/llm_factory.md](docs/llm_factory.md)** for detailed guide.

### 2. **Environment Configuration**

**Hierarchical loading strategy:**
- **Root `.env`** → Common variables (OLLAMA_*, VAULT_*, LANGFUSE_*, LOG_LEVEL)
- **Project `.env`** (optional) → Integration-specific variables (GITHUB_*, REDIS_*, PGVECTOR_*)

Simple projects use only root `.env`. Integration projects add their own `.env` for integration variables.

**Example root `.env` (required):**
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=                # Leave blank for local Ollama
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
LOG_LEVEL=INFO

# Langfuse (always-on by default)
LANGFUSE_ENABLED=true
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=http://localhost:3000

# Vault (optional, disabled by default)
VAULT_ENABLED=false
VAULT_ADDR=http://vault.example.com:8200
VAULT_TOKEN=hvs.your_vault_token
```

**Example project `.env` (integration-specific):**
```env
# projects/04_github_issue_reporter/.env
GITHUB_TOKEN=ghp_your_token
GITHUB_REPO_OWNER=your_org
GITHUB_REPO_NAME=your_repo
MS_TEAMS_WEBHOOK_URL=https://...webhook.office.com/...
```

See **[docs/getting_started.md](docs/getting_started.md)** for complete setup guide.

### 3. **Optional Enterprise Features**

#### **HashiCorp Vault** (Secret Management)
- Centralized secret storage for teams
- Automatic fallback to `.env` if Vault unreachable
- Zero code changes — transparent credential retrieval
- See **[docs/vault.md](docs/vault.md)** for setup

#### **Langfuse** (Observability)
- Always-on LLM tracing by default (`LANGFUSE_ENABLED=true`)
- Automatic cost tracking and performance analytics
- Works with Vault integration for secure key storage
- Graceful degradation if unavailable
- See **[docs/langfuse.md](docs/langfuse.md)** for dashboard guide

---

## Testing

**All code must maintain ≥75% test coverage** (enforced via `pytest.ini`).

```powershell
# Run tests with coverage report
pytest --cov --cov-report=term-missing

# Verify ≥75% coverage (fails if below threshold)
pytest --cov --cov-fail-under=75

# Run only unit tests (fast)
pytest -m unit
```

**Key principles:**
- All LLM/Ollama calls **must be mocked** (no real API calls in tests)
- Use shared fixtures from `common/tests/conftest.py`
- SDK auto-generates test templates with 75% coverage baseline

See **[docs/testing.md](docs/testing.md)** for comprehensive guide and **[docs/TESTING_STRATEGY.md](docs/TESTING_STRATEGY.md)** for philosophy.

---

## CI/CD & GitHub Copilot Integration

**Automated workflows powered by GitHub Actions:**

### **Key Features**
- **GitHub Copilot Integration** — Assign issues to Copilot with `/implement-plan` command
- **Automated Testing** — Run tests on every push with 75% coverage requirement
- **CODEOWNERS Approval** — Only authorized users can trigger implementation
- **Automated Staging** — Deploy to staging from `dev` branch automatically
- **Teams Notifications** — Rich adaptive cards in Microsoft Teams for PR events

### **Quick Commands**
```bash
# Trigger GitHub Copilot implementation (issue comment, CODEOWNERS only)
/implement-plan                                    # Uses defaults
/implement-plan branch=feature/auth model=gpt-4.1  # Custom config
```

### **Documentation**
- **[GitHub Copilot Integration](docs/github-copilot-integration.md)** — Complete workflow guide
- **[CI/CD Overview](docs/ci-cd.md)** — Pipeline architecture, deployment flows
- **[Teams Notifications](docs/teams-notifications.md)** — Webhook setup and card format

---

## Documentation

### **Getting Started**
| Guide | Goal |
|-------|------|
| **[Getting Started](docs/getting_started.md)** | Set up environment, configure Ollama (local or remote), troubleshoot connection issues |
| **[Prerequisites](docs/prerequisites.md)** | Install Python 3.10+, uv, Ollama, and verify system requirements |

### **Core Concepts**
| Guide | Goal |
|-------|------|
| **[SDK Documentation](docs/sdk.md)** | Use CLI to scaffold projects, compose integrations, validate structure |
| **[LLM Factory](docs/llm_factory.md)** | Choose correct LLM builder (`get_llm` vs `get_chat_llm`), swap models, debug issues |
| **[Models Reference](docs/models.md)** | Compare models, understand capabilities, pull and configure alternatives |

### **Enterprise Features**
| Guide | Goal |
|-------|------|
| **[HashiCorp Vault](docs/vault.md)** | Set up centralized secret management, configure team workflows |
| **[Langfuse Observability](docs/langfuse.md)** | Monitor LLM usage, track costs, analyze performance with dashboards |

### **Development**
| Guide | Goal |
|-------|------|
| **[Testing](docs/testing.md)** | Write effective tests, mock LLMs, achieve 75% coverage |
| **[Contributing](docs/contributing.md)** | Add new projects, follow naming conventions, maintain standards |
| **[CI/CD](docs/ci-cd.md)** | Understand deployment pipeline, configure automation, approve implementations |

### **Learning Resources**
| Resource | Topic |
|----------|-------|
| **[What Is Agentic AI](Quick-Reference/01_What_Is_Agentic_AI.md)** | Core concepts, definitions, patterns |
| **[ReAct Pattern](Quick-Reference/02_ReAct_Pattern_Deep_Dive.md)** | Reason + Act pattern, implementation guide |
| **[RAG Pipeline](Quick-Reference/03_RAG_Retrieval_Augmented_Generation.md)** | Vector stores, embeddings, retrieval strategies |
| **[Ollama Guide](Quick-Reference/04_Ollama.md)** | Model management, API reference, optimization |
| **[GitHub Copilot](Quick-Reference/05_GitHub_Copilot_Workspace_Integration.md)** | Workflow, best practices, interview Q&A |

---

## Contributing

**Goal**: Add high-quality projects that demonstrate specific patterns or integrations.

**How to contribute:**
1. **Use the SDK** (recommended): `ai-agent-builder new-project NN_your_project --arch [lcel|langgraph|custom]`
2. **Follow naming convention**: `NN_descriptive_name` (e.g., `05_pdf_qa_agent`)
3. **Include tests**: Achieve ≥75% coverage (`pytest --cov --cov-fail-under=75`)
4. **Document thoroughly**: Write comprehensive README in your project directory
5. **Update this README**: Add your project to the [Example Projects](#example-projects) table

See **[docs/contributing.md](docs/contributing.md)** for complete guidelines.

---

## License

[MIT](LICENSE) — Free to use, modify, and distribute.

---

**Built with ❤️ for the LangChain community**
