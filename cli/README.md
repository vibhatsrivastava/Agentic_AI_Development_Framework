# AI Agent Builder (`ai-agent-builder`)

A CLI tool for scaffolding production-ready LangChain projects with composable integrations.

## Features

- **Automated Project Scaffolding**: Generate complete project structure with one command
- **Built-in Production Foundations**: Rate limiting, retry logic, token counting, error handling
- **Composable Integrations**: Mix-and-match vector stores, caching, observability, document loaders
- **90% Test Coverage Enforcement**: Auto-generated test fixtures for all integrations
- **Environment Automation**: HashiCorp Vault integration, `.env` validation

## Installation

```powershell
# From repo root — installs ai-agent-builder as an isolated uv tool (no venv needed)
uv tool install ./cli
```

## Quick Start

### 1. Create a Basic LCEL Chain Project

```powershell
ai-agent-builder new-project 05_basic_chain --base lcel
```

### 2. Create a RAG Project with pgvector and Langfuse

```powershell
ai-agent-builder new-project 06_rag_example \
  --base lcel \
  --integrations pgvector,langfuse
```

### 3. Validate Project Structure

```powershell
ai-agent-builder validate projects/06_rag_example
```

### 4. Run Tests

```powershell
ai-agent-builder test projects/06_rag_example
```

### 5. List Available Integrations

```powershell
ai-agent-builder integrations list
```

## Available Integrations (v0.1.0)

### Vector Stores
- **Chroma**: Local vector store (default for RAG)
- **pgvector**: PostgreSQL + pgvector extension (production)
- **FAISS**: High-performance local vector search

### Caching
- **Redis**: Industry-standard LLM response caching

### Observability
- **Langfuse**: Open-source tracing and cost tracking

### Document Loaders
- **PDF Loader**: Load PDFs for RAG (PyPDF/PDFPlumber)
- **Web Scraper**: Scrape documentation/articles (BeautifulSoup4)

## Usage Examples

### Interactive Project Creation

```powershell
ai-agent-builder new-project 07_my_project

# Prompts:
# Project number: 07
# Project name: my_project
# Select base architecture:
#   [x] LCEL Chain
#   [ ] LangGraph Agent
# Select integrations:
#   [x] Chroma
#   [ ] pgvector
#   [x] Langfuse
```

### Get Integration Details

```powershell
ai-agent-builder integrations info pgvector

# Output:
# pgvector - PostgreSQL with pgvector extension
# 
# Dependencies:
#   - psycopg2-binary>=2.9.9
#   - pgvector>=0.2.4
#   - langchain-postgres>=0.0.3
# 
# Environment Variables:
#   - POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB
#   - POSTGRES_USER, POSTGRES_PASSWORD
# 
# Files Generated:
#   - src/db/vector_store.py
#   - src/db/schema.sql
# 
# Prerequisites:
#   - PostgreSQL 15+ with pgvector extension
```

## Development

### Running Tests

```powershell
cd cli/
pytest --cov=ai_agent_builder --cov-report=term-missing
```

### Building the Package

```powershell
cd cli/
python -m build
```

## Architecture

### Built-in vs Optional Integrations

**Built-in Integrations** (always available):
- Live in `common/` — imported by all projects
- Examples: Ollama LLM, Vault, rate limiting, retry logic
- SDK generates import statements only (no code duplication)

**Optional Integrations** (user-selected):
- Generate new files in `src/db/`, `src/cache/`, `src/monitoring/`
- Examples: pgvector, Redis, Langfuse
- SDK generates complete implementation + dependencies + .env vars

## Commands Reference

### `ai-agent-builder new-project`

Create a new LangChain project with scaffolding.

**Flags**:
- `--base {lcel,langgraph,custom}`: Base architecture (default: lcel)
- `--integrations <list>`: Comma-separated integration names
- `--template-dir <path>`: Custom template directory (advanced)

**Example**:
```powershell
ai-agent-builder new-project 08_production_rag \
  --base lcel \
  --integrations pgvector,redis,langfuse,pdf-loader
```

### `ai-agent-builder validate`

Validate project structure, environment variables, and test coverage.

**Example**:
```powershell
ai-agent-builder validate projects/08_production_rag
```

### `ai-agent-builder test`

Run pytest with coverage reporting.

**Example**:
```powershell
ai-agent-builder test projects/08_production_rag
```

### `ai-agent-builder integrations list`

List all available integrations with descriptions.

### `ai-agent-builder integrations info <name>`

Show detailed information about an integration.

## Roadmap

### v0.1.0 (Current)
- ✅ Core CLI infrastructure
- ✅ Built-in foundations (rate limiting, retry, token counting, caching)
- ✅ Optional integrations: Chroma, pgvector, FAISS, Redis, Langfuse, PDF, Web
- ✅ Project scaffolding automation
- ✅ Test generation with >=90% coverage enforcement

### v0.2.0 (Q2 2026)
- Add integrations: Pinecone, Weaviate, Qdrant, LangSmith, Supabase, MongoDB
- `ai-agent-builder add-integration` command (add to existing project)
- `ai-agent-builder migrate` command (update projects to new SDK version)
- Custom template directory support

### v0.3.0+ (Q3 2026)
- Specialized integrations: Neo4j, Elasticsearch, Kafka, Celery
- Custom integration plugin system
- Multi-project orchestration

### v1.0.0 (Q4 2026)
- Production stability guarantees
- PyPI distribution
- External adoption support (non-monorepo usage)

## Contributing

See [../docs/contributing.md](../docs/contributing.md) for development guidelines.

## License

MIT License - See [../LICENSE](../LICENSE) for details.

## Links

- **Documentation**: [../docs/sdk.md](../docs/sdk.md)
- **Repository**: https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework
- **Issues**: https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework/issues
