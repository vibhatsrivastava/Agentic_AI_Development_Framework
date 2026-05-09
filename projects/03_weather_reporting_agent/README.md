# 03_weather_reporting_agent — Weather Reporting Agent

LangGraph Agent implementation using LangChain

---

## Overview

This project was scaffolded using `ai-agent-builder` CLI tool.

**Architecture:** langgraph
**Project Number:** 03

---

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```powershell
cp .env.example .env
```

Required variables:
- `OLLAMA_BASE_URL` — Ollama server URL
- `OLLAMA_MODEL` — Default LLM model

### 2. Install Dependencies

```powershell
# Activate shared virtual environment
.venv\Scripts\Activate.ps1

# Install project-specific dependencies
pip install -r requirements.txt
```


---

## Usage

### Run the Project

```powershell
python src/main.py
```

### Run Tests

```powershell
# Run all tests with coverage
pytest --cov --cov-report=term-missing

# Run specific test file
pytest tests/test_main.py -v
```

---

## Project Structure

```
03_weather_reporting_agent/
├── src/
│   └── main.py           # Main entry point
├── tests/
│   ├── conftest.py       # pytest fixtures
│   └── test_main.py      # Unit tests
├── requirements.txt      # Project-specific dependencies
├── .env.example          # Environment variable template
└── README.md             # This file
```

---

## Development

### Testing Requirements

- Minimum 90% test coverage
- All LLM calls must be mocked in tests
- Run `pytest --cov --cov-fail-under=90` before committing

### Code Quality

- Follow repository conventions (see `docs/contributing.md`)
- Use `common/` package for LLM initialization, logging, utilities
- Always use LCEL for chain composition
- No project-level `.env` files (use root `.env`)

---

## Resources

- [Repository Docs](../../docs/getting_started.md)
- [LangChain Documentation](https://docs.langchain.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [Ollama Documentation](https://ollama.com/)

---

## License

See repository LICENSE file.
