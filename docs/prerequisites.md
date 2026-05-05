# Prerequisites

Ensure the following are in place before running any project in this repo.

---

## 1. Python

**Version:** Python 3.10 or higher

```bash
python --version    # should print 3.10+
```

Download from [https://www.python.org/downloads/](https://www.python.org/downloads/).

---

## 2. Ollama Access

Choose one of the following:

### Option A — Remote Hosted Server (Default)

- Request the **server URL** and **API key** from your admin.
- Verify access:

  ```bash
  curl -H "Authorization: Bearer your_api_key_here" https://your-ollama-server.example.com/api/tags
  ```

  A successful response returns a JSON object listing available models.

### Option B — Local Ollama Installation

- Download and install from [https://ollama.com/download](https://ollama.com/download)
- Verify installation:

  ```bash
  ollama --version
  curl http://localhost:11434/api/tags    # should return a JSON response
  ```

---

## 3. RAM / Hardware (Local Ollama Only)

Running large models locally requires sufficient memory:

| Model Size | Minimum RAM | Recommended RAM |
|-----------|------------|----------------|
| 1B–3B | 4 GB | 8 GB |
| 7B–8B | 8 GB | 16 GB |
| 13B–14B | 12 GB | 16 GB |
| 20B+ | 16 GB | 24 GB+ |

**GPU Acceleration (Optional):**
- NVIDIA GPU: Ollama auto-detects CUDA. Install the [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads).
- Apple Silicon (M1/M2/M3): GPU acceleration is enabled by default via Metal.
- Inference will fall back to CPU if no GPU is detected.

---

## 4. Git

```bash
git --version
```

Download from [https://git-scm.com/](https://git-scm.com/) if not installed.

---

## 5. uv (Package Manager)

[uv](https://docs.astral.sh/uv/) is the package manager used throughout this repo. It replaces `pip` and `python -m venv` and is significantly faster. Each project uses an isolated `.venv` created and managed by `uv`.

### Install uv (run once)

**Windows (standalone installer — no Python required):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Or via pip if Python is already installed:**
```bash
pip install uv
```

### Verify installation

```bash
uv --version    # should print uv x.x.x
```

### How virtual environments work in this repo

Each project under `projects/` has its own `.venv/` directory. The CLI (`ai-agent-builder new-project`) creates it automatically — no manual setup needed:

- Runs `uv venv .venv` inside the project folder
- Runs `uv pip install -r requirements-base.txt` (test tooling)
- Runs `uv pip install -e ./common` (installs `langchain`, `langgraph`, `langchain-ollama`, etc.)

For the **root-level test suite only**, create a root `.venv` manually:
```powershell
uv venv .venv
uv pip install -e ./common
uv pip install -r requirements-base.txt
```

### Activate a project virtual environment

After scaffolding, activate the project's `.venv` to run scripts:

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt / cmd.exe):**
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

Once activated, your shell prompt will be prefixed with `(.venv)`, confirming the environment is active.

### Deactivate when done

```bash
deactivate
```
