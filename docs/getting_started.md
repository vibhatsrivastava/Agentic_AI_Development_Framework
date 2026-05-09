# Getting Started

This guide walks you through setting up your environment to run any project in this monorepo.

---

## Prerequisites

Before you begin, complete the steps in [prerequisites.md](prerequisites.md).

---

## Option A — Remote / Company-Hosted Ollama (Default)

This is the standard setup when using the shared `gpt-oss:20b` model on a hosted server.

### 1. Clone the Repository

```bash
git clone https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework.git
cd Agentic_AI_Development_Framework
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your values:

```dotenv
OLLAMA_BASE_URL=https://your-ollama-server.example.com   # Provided by your admin
OLLAMA_API_KEY=your_api_key_here                         # Provided by your admin
OLLAMA_MODEL=gpt-oss:20b
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

> **Note:** Never commit your `.env` file. It is listed in `.gitignore`.

### 3. Create and Activate a Virtual Environment

> Install `uv` first if you haven't: see [prerequisites.md](prerequisites.md#5-uv-package-manager).

```powershell
# From the repo root
uv venv .venv
```

Activate it before installing anything or running any script:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

Your prompt will show `(.venv)` when the environment is active. See [prerequisites.md](prerequisites.md) for more details.

### 4. Install Base Dependencies

```powershell
# Test tooling (pytest, etc.)
uv pip install -r requirements-base.txt

# Runtime dependencies: langchain, langgraph, langchain-ollama, etc.
uv pip install -e ./common
```

### 5. Run a Project

```powershell
cd projects/01_hello_langchain
python src/main.py
```

### 5. Verify Connectivity (Optional)

```bash
curl -H "Authorization: Bearer your_api_key_here" https://your-ollama-server.example.com/api/tags
```

You should see a JSON list of available models on the server.

---

## Option B — Local Ollama (Self-Hosted)

Use this if you want to run models entirely on your own machine without any server access.

### 1. Install Ollama

Download and install from [https://ollama.com/download](https://ollama.com/download).

On Windows, the installer adds Ollama as a background service. On macOS/Linux:

```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve   # start the server (runs on http://localhost:11434)
```

### 2. Pull a Model

```bash
ollama pull gpt-oss:20b              # default model (if available locally)
# OR any alternative model:
ollama pull llama3.1:8b
ollama pull mistral:7b
```

See [models.md](models.md) for a full list of recommended models and pull commands.

### 3. Configure Environment Variables

```bash
cp .env.example .env
```

Update `.env` for local use:

```dotenv
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=                        # Leave blank — no auth for local Ollama
OLLAMA_MODEL=gpt-oss:20b               # Or whichever model you pulled
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

### 4. Pull Embedding Model

```bash
ollama pull nomic-embed-text           # required for RAG/embedding projects
```

### 5. Create and Activate a Virtual Environment

```powershell
# From the repo root
uv venv .venv
```

Activate before installing packages or running scripts:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 6. Install & Run

```powershell
# Test tooling
uv pip install -r requirements-base.txt

# Runtime dependencies: langchain, langgraph, langchain-ollama, etc.
uv pip install -e ./common

cd projects/01_hello_langchain
python src/main.py
```

---

## Shared `common/` Library

All projects import from the `common/` package directly. The `common/` package is installed as an editable package (`ai-agent-common`) into each project's `.venv` by the CLI scaffold — no `sys.path` manipulation needed:

```python
# Direct import — works because ai-agent-common is installed in the project venv
from common.llm_factory import get_llm, get_embeddings
from common.utils import get_logger

logger = get_logger(__name__)
llm = get_llm()                          # uses OLLAMA_MODEL from .env
llm = get_llm(model="gpt-oss:20b")      # override per-call
```

---

## Optional: HashiCorp Vault Integration

For teams with multiple developers, you can use **HashiCorp Vault** to centrally manage API keys instead of distributing them via `.env` files.

### Why Use Vault?

- **Centralized secrets**: Store `OLLAMA_API_KEY` once in Vault, accessible to all developers on the network
- **Automatic fallback**: If Vault is unreachable (offline, network issues), applications use `.env` as fallback
- **Zero code changes**: Projects continue using `get_llm()` — credential retrieval is transparent
- **Backward compatible**: Vault is disabled by default; existing workflows unchanged

### Quick Setup

1. **Ask your team lead for Vault credentials:**
   - Vault server URL
   - Vault authentication token

2. **Enable Vault in your `.env`:**
   ```env
   VAULT_ENABLED=true
   VAULT_ADDR=http://vault.example.com:8200
   VAULT_TOKEN=hvs.your_vault_token_here
   ```

3. **Run your project** — API keys are automatically retrieved from Vault:
   ```powershell
   python projects/01_hello_langchain/src/main.py
   ```

4. **Verify in logs:**
   ```
   INFO | common.vault | Retrieved 'OLLAMA_API_KEY' from Vault (path: secret/ollama)
   ```

### Full Documentation

For complete setup instructions, troubleshooting, and security best practices, see:

**[docs/vault.md](vault.md)** — Comprehensive HashiCorp Vault integration guide

Topics covered:
- Setting up a local Vault dev server
- Configuring a production Vault instance
- Storing and rotating secrets
- Testing Vault connectivity
- Troubleshooting common issues
- Advanced authentication methods (AppRole, etc.)

---

## Environment Variable Management

**All environment variables are configured in the root `.env` file.** The `load_dotenv()` function automatically searches upward from the `common/` directory and finds the root `.env` file, making it available to all projects.

Project-specific variables (if any) are documented in the project's `README.md` and added to the root `.env.example` with clear comments indicating which project uses them.
