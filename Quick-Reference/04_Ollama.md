# 04 — Ollama

> **Audience:** Beginners in Agentic AI | **Focus:** What · Why · When · How + Technical Interview Prep  
> **References:** [Ollama Official Site](https://ollama.com/) · [Ollama GitHub](https://github.com/ollama/ollama) · [Ollama Model Library](https://ollama.com/library) · [Ollama REST API Docs](https://github.com/ollama/ollama/blob/main/docs/api.md)

---

## Table of Contents

1. [What is Ollama?](#1-what-is-ollama)
2. [Why Use Ollama?](#2-why-use-ollama)
3. [When to Use Ollama](#3-when-to-use-ollama)
4. [How Ollama Works](#4-how-ollama-works)
5. [Installing and Running Ollama](#5-installing-and-running-ollama)
6. [Key Ollama Commands](#6-key-ollama-commands)
7. [Ollama REST API](#7-ollama-rest-api)
8. [Ollama in This Repo](#8-ollama-in-this-repo)
9. [Ollama vs Cloud LLM APIs](#9-ollama-vs-cloud-llm-apis)
10. [Interview Cheat Sheet](#10-interview-cheat-sheet)

---

## 1. What is Ollama?

### Simple Definition

**Ollama** is an open-source tool that lets you **download, run, and serve large language models (LLMs) locally on your own machine** — with a single command.

It packages model weights, configuration, and a runtime into a single binary that:
- Exposes an **OpenAI-compatible REST API** on `http://localhost:11434`
- Manages model storage, loading, and unloading automatically
- Works on macOS, Linux, and Windows (with GPU and CPU support)

### Everyday Analogy

> Think of Ollama like **Docker, but for LLMs**.  
> Just as Docker pulls a container image and runs it locally, Ollama pulls a model and runs it locally — giving you a private, offline AI server on your own hardware.

### One-Line Summary

> _Ollama is a local LLM runtime that lets you run open-source models like Llama 3, Mistral, and Gemma on your own machine via a simple CLI and REST API._

---

## 2. Why Use Ollama?

| Reason | Detail |
|---|---|
| **Privacy** | Data never leaves your machine — no cloud provider sees your prompts |
| **No API costs** | No per-token billing — unlimited requests on your own hardware |
| **No internet required** | Works fully offline after the model is downloaded |
| **Easy model switching** | `ollama pull <model>` downloads any model in minutes |
| **OpenAI-compatible API** | Works with any SDK or framework that supports the OpenAI API format |
| **No GPU required** | Runs on CPU (slower) or GPU (fast) — works on a laptop |
| **Supports many model families** | Llama, Mistral, Gemma, Phi, DeepSeek, Qwen, and more |

---

## 3. When to Use Ollama

| Use Ollama When… | Don't Use Ollama When… |
|---|---|
| You need **privacy** — prompts contain sensitive or proprietary data | You need the absolute best model quality (GPT-4, Claude, Gemini Ultra) |
| You are **prototyping** and want to avoid API costs | You have no local hardware (only a browser / Colab) |
| You need to work **offline** | You need multi-modal capabilities not yet in open models |
| You want **full control** over the model version | You need production-grade SLAs and uptime guarantees |
| You are **learning** Agentic AI without a cloud account | Your team needs a managed, scalable inference endpoint |
| You want to run a **shared team server** with Ollama hosted centrally | — |

---

## 4. How Ollama Works

### Architecture

```
┌──────────────────────────────────────────────────┐
│                  Your Machine                    │
│                                                  │
│   ┌─────────────────────────────────────────┐    │
│   │          Ollama Server Process          │    │
│   │                                         │    │
│   │  ┌───────────┐    ┌──────────────────┐  │    │
│   │  │ REST API  │    │  Model Runtime   │  │    │
│   │  │ :11434    │◄──►│  (llama.cpp)     │  │    │
│   │  └───────────┘    └────────┬─────────┘  │    │
│   │                            │             │    │
│   │                  ┌─────────▼──────────┐  │    │
│   │                  │   Model Weights    │  │    │
│   │                  │  (~/.ollama/models)│  │    │
│   │                  └────────────────────┘  │    │
│   └─────────────────────────────────────────┘    │
│                                                  │
│   Your App / LangChain / curl                    │
│         │                                        │
│         └──► HTTP POST localhost:11434/api/chat  │
└──────────────────────────────────────────────────┘
```

### What Happens When You Run a Model

```
1. ollama run llama3.1:8b
        │
        ▼
2. Ollama checks ~/.ollama/models for cached weights
        │
   ┌────▼──────────────────────────────┐
   │ Model not cached?                 │
   │   → Download from Ollama registry │
   │ Model cached?                     │
   │   → Load directly from disk       │
   └────┬──────────────────────────────┘
        │
        ▼
3. Ollama loads model into RAM / VRAM
        │
        ▼
4. REST API becomes available at localhost:11434
        │
        ▼
5. Accept prompt → run inference → stream response
```

### Under the Hood

| Component | What It Is |
|---|---|
| **llama.cpp** | The underlying C++ inference engine that runs the model on CPU/GPU |
| **GGUF format** | The model file format Ollama uses — quantised weights that fit in RAM |
| **Quantisation** | Compression technique that reduces model size (e.g., 8B model ≈ 4.7 GB at Q4) |
| **Modelfile** | A configuration file (like a Dockerfile) that defines a model's base, system prompt, and parameters |
| **Model registry** | `ollama.com/library` — the central repository of available models |

---

## 5. Installing and Running Ollama

### Installation

| Platform | Command |
|---|---|
| **macOS** | `brew install ollama` or download from ollama.com |
| **Linux** | `curl -fsSL https://ollama.com/install.sh \| sh` |
| **Windows** | Download the installer from ollama.com |

### Start the Server

```bash
ollama serve
# Server starts at http://localhost:11434
# (On macOS/Linux it starts automatically as a background service after install)
```

### Pull and Run a Model

```bash
# Pull a model (download only, don't start a chat)
ollama pull llama3.1:8b

# Pull and immediately start an interactive chat
ollama run llama3.1:8b

# Run a one-shot prompt (non-interactive)
ollama run llama3.1:8b "Explain RAG in one sentence."
```

### Model Storage Location

| Platform | Default Path |
|---|---|
| macOS / Linux | `~/.ollama/models/` |
| Windows | `C:\Users\<user>\.ollama\models\` |

---

## 6. Key Ollama Commands

| Command | Description |
|---|---|
| `ollama pull <model>` | Download a model from the Ollama registry |
| `ollama run <model>` | Start an interactive chat with a model |
| `ollama list` | Show all locally downloaded models |
| `ollama show <model>` | Show model details (parameters, template, licence) |
| `ollama rm <model>` | Delete a local model to free disk space |
| `ollama ps` | Show currently loaded models and memory usage |
| `ollama serve` | Start the Ollama server (API on port 11434) |
| `ollama create <name> -f Modelfile` | Create a custom model from a Modelfile |
| `ollama cp <src> <dst>` | Copy a model under a new name |

### Useful Model Name Formats

```
llama3.1:8b          # model:tag (specific version)
llama3.1             # model (pulls the default/latest tag)
llama3.1:70b         # larger variant of the same model family
mistral:7b-instruct  # instruction-tuned variant
nomic-embed-text     # an embedding model
```

---

## 7. Ollama REST API

Ollama exposes an **OpenAI-compatible REST API** at `http://localhost:11434`. Any tool that can talk to OpenAI can talk to Ollama by changing the base URL.

### Key Endpoints

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/generate` | POST | Raw text completion (non-chat) |
| `/api/chat` | POST | Chat completion with message roles |
| `/api/embeddings` | POST | Generate embeddings for a text input |
| `/api/tags` | GET | List all locally available models |
| `/api/show` | POST | Show details for a specific model |
| `/api/pull` | POST | Pull a model programmatically |

### Chat Completion Example (curl)

```bash
curl http://localhost:11434/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3.1:8b",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user",   "content": "What is LangChain?"}
    ],
    "stream": false
  }'
```

### Authenticated Server (Remote Ollama)

When Ollama is hosted on a remote server with a Bearer token:

```bash
curl https://your-ollama-server.example.com/api/chat \
  -H "Authorization: Bearer your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-oss:20b", "messages": [...], "stream": false}'
```

This is how `common/llm_factory.py` in this repo connects to the hosted Ollama server — by passing the auth header via `client_kwargs`.

### List Available Models (curl)

```bash
# Local
curl http://localhost:11434/api/tags

# Remote with auth
curl -H "Authorization: Bearer your_api_key_here" \
     https://your-ollama-server.example.com/api/tags
```

---

## 8. Ollama in This Repo

### How the Repo Uses Ollama

All LLM calls in this repository go through `common/llm_factory.py`, which wraps three `langchain_ollama` classes:

```
.env file
  OLLAMA_BASE_URL        = http://localhost:11434   (or remote server URL)
  OLLAMA_API_KEY         = (blank for local, token for remote)
  OLLAMA_MODEL           = gpt-oss:20b
  OLLAMA_EMBEDDING_MODEL = nomic-embed-text
        │
        ▼
common/llm_factory.py
  get_llm()          → OllamaLLM        (raw string completion)
  get_chat_llm()     → ChatOllama       (chat / agents)
  get_embeddings()   → OllamaEmbeddings (RAG / vector stores)
        │
        ▼
langchain_ollama library
        │
        ▼
Ollama REST API  →  localhost:11434  or  remote server
        │
        ▼
Model (gpt-oss:20b, llama3.1:8b, nomic-embed-text, etc.)
```

### Switching Between Local and Remote Ollama

```dotenv
# .env — Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=
OLLAMA_MODEL=llama3.1:8b

# .env — Remote hosted Ollama
OLLAMA_BASE_URL=https://your-ollama-server.example.com
OLLAMA_API_KEY=your_bearer_token_here
OLLAMA_MODEL=gpt-oss:20b
```

No code changes are needed — `llm_factory.py` reads these values at startup.

### Recommended Models for This Repo

| Model | Use Via | Best For |
|---|---|---|
| `gpt-oss:20b` | `get_llm()` / `get_chat_llm()` | Default — agents, reasoning (hosted server) |
| `llama3.1:8b` | `get_llm()` / `get_chat_llm()` | Local development — good balance of speed and quality |
| `mistral:7b` | `get_llm()` / `get_chat_llm()` | Instruction following, fast responses |
| `nomic-embed-text` | `get_embeddings()` | RAG pipelines — default embedding model |
| `mxbai-embed-large` | `get_embeddings()` | Higher quality embeddings |

---

## 9. Ollama vs Cloud LLM APIs

| Dimension | Ollama (Local/Self-hosted) | Cloud APIs (OpenAI, Anthropic, Google) |
|---|---|---|
| **Privacy** | ✅ Data stays on your machine | ❌ Data sent to third-party servers |
| **Cost** | ✅ Free (electricity only) | 💰 Per-token billing |
| **Model quality** | Good (open-source models) | Best (GPT-4, Claude 3.5, Gemini Ultra) |
| **Setup** | One-time install + model download | API key only |
| **Internet required** | Only for model download | Always |
| **Rate limits** | None | Yes (requests per minute/day) |
| **Latency** | Depends on hardware | Low (optimised cloud infra) |
| **Model variety** | 100+ open-source models | Limited to provider's models |
| **Customisation** | Full (Modelfile, fine-tuning) | Limited (system prompt, fine-tune API) |
| **Production scale** | Requires self-managed infra | Managed, auto-scales |

### Decision Guide

```
Need privacy or working with sensitive data?
    └──► Ollama (local or self-hosted)

Learning / prototyping with no budget?
    └──► Ollama (local)

Need best-in-class model quality for production?
    └──► Cloud API (OpenAI / Anthropic)

Need both privacy AND scale?
    └──► Self-hosted Ollama on a dedicated GPU server
         (This repo's setup: remote Ollama server with Bearer auth)
```

---

## 10. Interview Cheat Sheet

| Question | Key Answer |
|---|---|
| **What is Ollama?** | An open-source tool that runs LLMs locally by exposing an OpenAI-compatible REST API at `localhost:11434` — like Docker, but for LLMs |
| **What inference engine does Ollama use under the hood?** | `llama.cpp` — a C++ runtime that runs quantised GGUF model files on CPU or GPU |
| **What is GGUF?** | The model file format Ollama uses — quantised (compressed) model weights that fit in RAM, traded some precision for dramatically smaller file size |
| **What is quantisation?** | A compression technique that reduces model weight precision (e.g., from 32-bit float to 4-bit integer), shrinking a 70B model from ~140 GB to ~40 GB with modest quality loss |
| **What port does Ollama listen on?** | `11434` by default |
| **How is the Ollama API compatible with OpenAI?** | It supports the same `/api/chat` endpoint format with `role`/`content` message objects, so any OpenAI SDK client can point its `base_url` at Ollama instead |
| **What is a Modelfile?** | A configuration file (similar to a Dockerfile) that defines a custom model — its base model, system prompt, temperature, and other parameters |
| **How does this repo connect to Ollama?** | Via `common/llm_factory.py`, which reads `OLLAMA_BASE_URL`, `OLLAMA_API_KEY`, and `OLLAMA_MODEL` from `.env` and passes them to `langchain_ollama` classes |
| **What is `langchain_ollama`?** | A LangChain integration package (`pip install langchain-ollama`) that wraps Ollama's API into LangChain-compatible classes: `OllamaLLM`, `ChatOllama`, and `OllamaEmbeddings` |
| **How do you switch models without changing code?** | Change `OLLAMA_MODEL` in `.env` — `llm_factory.py` reads it at startup. Or pass `model=` directly to `get_llm()` / `get_chat_llm()` for a per-call override |
| **What is the difference between `OllamaLLM` and `ChatOllama`?** | `OllamaLLM` is for raw string completion (single-turn). `ChatOllama` is for chat-style interactions with message roles (system/human/ai) — required for agents and multi-turn conversations |
| **How do you run Ollama on a remote server with authentication?** | Set `OLLAMA_BASE_URL` to the remote URL and `OLLAMA_API_KEY` to the Bearer token. `llm_factory.py` injects the `Authorization` header via `client_kwargs` |

---

*Previous: [03_RAG_Retrieval_Augmented_Generation.md](03_RAG_Retrieval_Augmented_Generation.md)*  
*Next in Quick-Reference → `05_LangChain_Core_Concepts.md`*
