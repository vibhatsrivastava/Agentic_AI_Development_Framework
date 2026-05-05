# 01 — Hello LangChain

Minimal working example demonstrating a basic LangChain LCEL chain using an Ollama-hosted LLM.

---

## What This Project Covers

- Loading a model via the shared `common/llm_factory` utility
- Defining a `PromptTemplate`
- Building a simple **LCEL chain**: `prompt | llm | StrOutputParser()`
- Running a single Q&A inference call

---

## How to Run

**1. Ensure the root `.env` is configured:**

```bash
# From the repo root
cp .env.example .env
# Fill in OLLAMA_BASE_URL and OLLAMA_API_KEY
```

**2. Set up and activate the virtual environment:**

If you scaffolded this project with `ai-agent-builder`, the `.venv` was created automatically with all dependencies installed. If not, create it manually:

```powershell
# From the repo root
uv venv projects/01_hello_langchain/.venv
```

Then activate it before installing dependencies:

_Windows (PowerShell):_
```powershell
cd projects/01_hello_langchain
.venv\Scripts\Activate.ps1
```

_macOS / Linux:_
```bash
cd projects/01_hello_langchain
source .venv/bin/activate
```

**3. Install dependencies:**

```powershell
# From the repo root (with venv activated)
uv pip install -e ./common
uv pip install -r requirements-base.txt
```

**4. Run:**

```bash
python src/main.py
```

**5. Deactivate when done:**

```bash
deactivate
```

---

## Sample Output

```
2026-03-20 10:00:00 | INFO | __main__ | Initialising LLM...
2026-03-20 10:00:00 | INFO | __main__ | Question: What is LangChain and why is it useful for building AI agents?

--- Response ---
LangChain is an open-source framework that simplifies building applications powered by large language
models (LLMs). It provides abstractions for chaining prompts, tools, memory, and retrieval steps,
making it easy to compose complex agentic workflows without managing low-level API calls directly.
----------------
```

---

## Notes / References

- [LangChain LCEL Docs](https://python.langchain.com/docs/concepts/lcel/)
- [OllamaLLM Integration](https://python.langchain.com/docs/integrations/llms/ollama/)
- To use a different model, set `OLLAMA_MODEL` in your `.env` — see [docs/models.md](../../docs/models.md)
