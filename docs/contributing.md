# Contributing — Adding a New Project

This guide explains the conventions for adding a new project to the monorepo.

---

## Project Naming

Projects live under `projects/` and follow this naming pattern:

```
NN_short_descriptive_name
```

- `NN` — two-digit sequential number (e.g. `01`, `02`, `03`)
- `short_descriptive_name` — lowercase, underscores, concise

**Examples:**
```
01_hello_langchain
02_rag_with_pdf
03_react_agent_tools
04_multi_agent_langgraph
```

---

## Required Scaffold

Every project **must** contain:

```
projects/NN_project_name/
├── src/
│   └── main.py              # Entry point
├── requirements.txt         # Project-specific deps (delta on top of requirements-base.txt)
└── README.md                # Project documentation (see template below)
```

**Important**: Do NOT create project-level `.env` or `.env.example` files. All environment variables must be defined in the root-level `.env.example` and documented in the project's README if they're project-specific.

---

## `requirements.txt` Convention

List **only the dependencies your project adds** beyond `requirements-base.txt`. Do not repeat base deps.

```text
# requirements.txt — project-specific additions only
chromadb          # vector store for this RAG project
pypdf             # PDF loader
```

---

## `README.md` Template

Each project must have a `README.md` following this structure:

```markdown
# Project Title

One-line description of what this project demonstrates.

## What This Project Covers
- Concept A
- Concept B

## How to Run
Steps to run this specific project.

## Sample Output
Paste a representative example of what the output looks like.

## Notes / References
Any caveats, links to relevant LangChain docs, etc.
```

---

## Importing from `common/`

Projects should use the shared `common/` library wherever possible to avoid duplicating LLM setup code.

Add this block at the top of `src/main.py`:

```python
import sys
import os

# Allow importing from the repo root's common/ package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from common.llm_factory import get_llm, get_embeddings
from common.utils import get_logger
```

---

## Environment Variable Convention

**All environment variables must be defined in the root `.env.example` file.** Do not create project-level `.env` or `.env.example` files.

If your project requires project-specific environment variables:

1. Add them to the root [`.env.example`](../.env.example) with clear comments indicating which project uses them
2. Document them in your project's `README.md` under an "Environment Variables" section

```markdown
## Environment Variables

This project uses the following variables from the root `.env` file:

- `OLLAMA_BASE_URL` — Ollama server endpoint (required)
- `OLLAMA_MODEL` — Default LLM model (required)
- `PDF_SOURCE_PATH` — Path to PDF file for ingestion (optional, defaults to `data/sample.pdf`)

See [.env.example](../../.env.example) for configuration details.
```

Example root `.env.example` entry:

```dotenv
# ─── Project-Specific Variables ─────────────────────────────
# PDF source path for 02_rag_with_pdf project
PDF_SOURCE_PATH=data/sample.pdf
```

---

## Updating the Root README

After adding your project, add a row to the **Projects** table in the root [README.md](../README.md):

```markdown
| 02 | [RAG with PDF](projects/02_rag_with_pdf/) | Retrieval-Augmented Generation over a local PDF using Chroma |
```

---

## Checklist Before Committing

- [ ] Project follows the `NN_name` naming convention
- [ ] `src/main.py` is present and runnable
- [ ] `requirements.txt` lists only project-specific deps
- [ ] `.env.example` is present (even if empty)
- [ ] `README.md` follows the template above
- [ ] Root `README.md` projects table is updated
- [ ] No `.env` file committed (confirm with `git status`)
- [ ] No API keys or secrets hardcoded in source files
