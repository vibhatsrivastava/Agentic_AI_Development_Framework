# 04 — GitHub Issue Reporter & Solution Recommender Agent

> **Architecture:** LangGraph ReAct Agent  
> **Difficulty:** Intermediate  
> **LangChain Components:** `ChatOllama`, `create_react_agent`, `@tool`, GitHub REST API  
> **Status:** ✅ Production Ready

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Benefits & Use Cases](#benefits--use-cases)
4. [Architecture](#architecture)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Configuration](#configuration)
8. [Usage](#usage)
9. [Deployment](#deployment)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)
12. [Security Considerations](#security-considerations)
13. [Performance & Limitations](#performance--limitations)
14. [Contributing](#contributing)

---

## Overview

The **GitHub Issue Reporter & Solution Recommender Agent** is an AI-powered tool that helps development teams manage GitHub repository issues more efficiently. It operates in two modes:

1. **Report Mode** (`--report`): Generates a comprehensive markdown report of all open issues in a repository, including metadata like age, assignees, labels, and last update time.

2. **Recommendation Mode** (`--issue N`): Analyzes a specific issue and provides AI-generated recommendations for resolution, including root cause analysis (for bugs) or implementation approaches (for features).

This agent uses LangGraph's ReAct (Reasoning + Acting) pattern to orchestrate multiple GitHub API tools and an LLM to provide intelligent insights.

---

## Features

### Core Capabilities

✅ **Automated Issue Reporting**
- Fetches all open issues from a GitHub repository
- Displays issue metadata in a structured markdown table
- Calculates issue age and staleness metrics
- Handles pagination automatically (up to 200 issues)
- Excludes pull requests from the issue list

✅ **AI-Powered Recommendations**
- Analyzes issue content including title, body, labels, and comments
- Provides structured recommendations based on issue type:
  - **Bugs:** Root cause hypothesis, affected area, suggested fix, test cases
  - **Features:** Implementation approach, design notes, acceptance criteria
- Grounds recommendations in actual issue data (no hallucination)
- Handles prompt injection attacks with safe content processing

✅ **Robust Error Handling**
- Graceful handling of HTTP errors (404, 403, 429)
- Clear error messages for configuration issues
- Input validation for issue numbers
- Automatic retry and rate limiting support

✅ **Security Hardened**
- Secure token management via environment variables
- Content truncation to prevent context overflow
- Prompt injection mitigation with XML delimiters
- No sensitive data logging

---

## Benefits & Use Cases

### For Development Teams

1. **Faster Issue Triage**
   - Quickly audit the entire issue backlog without clicking through GitHub UI
   - Identify stale issues that need attention
   - See priority distribution at a glance

2. **Accelerated Onboarding**
   - New team members can get AI-generated context for unfamiliar issues
   - Reduces time spent reading through long issue threads
   - Provides starting points for implementation

3. **Enhanced Code Quality**
   - AI-generated test case suggestions for bugs
   - Acceptance criteria recommendations for features
   - Root cause analysis helps prevent recurring issues

4. **Better Project Management**
   - Age and staleness metrics help prioritize work
   - Unassigned issues are highlighted
   - Label distribution shows work categories

### For Individual Developers

1. **Quick Issue Understanding**
   - Get a summary and action plan for complex issues
   - Identify affected code areas before diving in
   - Leverage LLM reasoning on multi-comment threads

2. **Implementation Guidance**
   - Suggested approaches for feature requests
   - Design considerations for complex changes
   - Test coverage recommendations

---

## Architecture

### High-Level Design

```
User CLI
  ↓
Argument Parser (--report | --issue N)
  ↓
Agent Orchestrator (LangGraph ReAct)
  ↓
GitHub API Tools (list_open_issues, get_issue_details, get_issue_comments)
  ↓
LLM Reasoning (ChatOllama)
  ↓
Structured Output (Markdown Report or Recommendation)
```

### Components

| Component | Technology | Purpose |
|---|---|---|
| **CLI** | Python `argparse` | User interface and argument validation |
| **Agent Core** | LangGraph `create_react_agent` | Orchestrates tool calls and LLM reasoning |
| **LLM** | Ollama (ChatOllama) | Reasoning, analysis, and output formatting |
| **Tools** | `@tool` decorators | GitHub REST API integration |
| **HTTP Client** | `requests` | External API communication |
| **Logging** | `common.utils.get_logger` | Structured logging and debugging |

### Tool Descriptions

1. **`list_open_issues(owner, repo)`**
   - Fetches all open issues (paginated, max 2 pages)
   - Computes age and staleness metrics
   - Excludes pull requests
   - Returns JSON with issue metadata

2. **`get_issue_details(owner, repo, issue_number)`**
   - Fetches single issue details
   - Truncates body to 4000 chars (context window protection)
   - Returns JSON with full issue data

3. **`get_issue_comments(owner, repo, issue_number)`**
   - Fetches top 10 comments for an issue
   - Truncates each comment to 1000 chars
   - Returns JSON with comment metadata

---

## Prerequisites

### System Requirements

- **Python:** 3.11 or higher
- **Ollama:** Installed and running (local or remote)
- **Operating System:** Windows, macOS, or Linux
- **Network:** Internet access for GitHub API calls

### Required Tools

```powershell
# Check Python version
python --version  # Should be 3.11+

# Check Ollama installation
ollama --version

# Verify Ollama is running
ollama list
```

### GitHub Personal Access Token

You need a GitHub Personal Access Token (PAT) with appropriate scopes:

1. Navigate to [GitHub Settings > Developer Settings > Personal Access Tokens > Tokens (classic)](https://github.com/settings/tokens)
2. Click **Generate new token (classic)**
3. Configure token:
   - **Name:** `Agentic AI Issue Reporter`
   - **Expiration:** Choose appropriate duration
   - **Scopes:**
     - For **public repositories:** Select `public_repo`
     - For **private repositories:** Select `repo` (full repo access)
4. Click **Generate token**
5. **IMPORTANT:** Copy the token immediately (you won't see it again)

---

## Installation & Setup

### Step 1: Clone Repository (if not already done)

```powershell
git clone https://github.com/vibhatsrivastava/Agentic_AI_Development_Framework.git
cd Agentic_AI_Development_Framework
```

### Step 2: Verify Root Environment Configuration

Ensure the root `.env` file exists and has required base variables:

```powershell
# Check root .env exists
Get-Content .env
```

If it doesn't exist, copy from example:

```powershell
Copy-Item .env.example .env
```

### Step 3: Activate Project Virtual Environment

The project's virtual environment was created during scaffolding:

```powershell
cd projects\04_github_issue_reporter
.venv\Scripts\Activate.ps1
```

On macOS/Linux:

```bash
cd projects/04_github_issue_reporter
source .venv/bin/activate
```

### Step 4: Install Dependencies

Dependencies should already be installed during scaffolding. To reinstall or update:

```powershell
# Ensure you're in the project directory with venv activated
uv pip install -r requirements.txt
uv pip install -e ../../common
```

### Step 5: Verify Installation

```powershell
# Check installed packages
uv pip list | Select-String -Pattern "langchain|requests|ollama"

# Verify common package is accessible
python -c "from common.llm_factory import get_chat_llm; print('✅ Common package imported successfully')"
```

---

## Configuration

### Environment Variables

All configuration is managed in the **root `.env` file** (not project-level). Add these variables:

```env
# === GitHub Configuration ===
GITHUB_TOKEN=ghp_your_personal_access_token_here
GITHUB_REPO_OWNER=your_github_username_or_org
GITHUB_REPO_NAME=your_repository_name

# === Ollama Configuration ===
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_API_KEY=  # Leave blank for local; set Bearer token for remote
OLLAMA_MODEL=llama3.2:3b  # Or any chat model you have installed
OLLAMA_EMBEDDING_MODEL=nomic-embed-text

# === Logging ===
LOG_LEVEL=INFO  # DEBUG for troubleshooting
```

### Configuration Details

| Variable | Required | Description | Example |
|---|---|---|---|
| `GITHUB_TOKEN` | ✅ Yes | GitHub Personal Access Token | `ghp_abc123...` |
| `GITHUB_REPO_OWNER` | ✅ Yes | Repository owner (user or org) | `vibhatsrivastava` |
| `GITHUB_REPO_NAME` | ✅ Yes | Repository name | `Agentic_AI_Development_Framework` |
| `OLLAMA_BASE_URL` | ✅ Yes | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_API_KEY` | ⚠️ Conditional | Required for remote Ollama | `Bearer token` |
| `OLLAMA_MODEL` | ✅ Yes | LLM model name | `llama3.2:3b` |
| `LOG_LEVEL` | ❌ Optional | Logging verbosity | `INFO`, `DEBUG` |

### Security Best Practices

⚠️ **NEVER commit `.env` files to version control!**

```powershell
# Verify .env is gitignored
git check-ignore .env
# Should output: .env
```

🔒 **Token Permissions:** Use the principle of least privilege. Grant only necessary scopes.

🔐 **Token Storage:** For teams, consider using HashiCorp Vault (see [docs/vault.md](../../docs/vault.md)).

---

## Usage

### Basic Commands

#### Report Mode: List All Open Issues

```powershell
# Activate venv (if not already active)
.venv\Scripts\Activate.ps1

# Generate issue report
python src\main.py --report
```

**Example Output:**

```markdown
================================================================================
## Open Issues Report — vibhatsrivastava/Agentic_AI_Development_Framework
**Total open issues: 4** | Generated: 2026-05-06

| # | Title | Author | Assignee | Labels | Opened | Age (days) | Last Updated | URL |
|---|---|---|---|---|---|---|---|---|
| 42 | Fix token counter edge case | alice | bob | bug, priority:high | 2026-04-01 | 35 | 2 days ago | [#42](https://github.com/...) |
| 38 | Add Redis caching integration | carol | Unassigned | enhancement | 2026-03-15 | 52 | 10 days ago | [#38](https://github.com/...) |
| 31 | LLM factory streaming support | alice | alice | feature | 2026-02-20 | 75 | 25 days ago | [#31](https://github.com/...) |
| 12 | Update vault documentation | dave | Unassigned | docs | 2025-12-01 | 156 | 60 days ago | [#12](https://github.com/...) |
================================================================================
```

#### Recommendation Mode: Analyze Specific Issue

```powershell
# Get recommendation for issue #42
python src\main.py --issue 42
```

**Example Output:**

```markdown
================================================================================
## Recommendation for Issue #42 — Fix token counter edge case

**Issue Type:** Bug

**Root Cause Hypothesis:**
The `token_counter.py` module calls `split()` on the input string without first 
checking for empty or whitespace-only input. When an empty string is passed, 
`split()` returns `[]` and downstream count calculation divides by zero.

**Affected Area:**
`common/token_counter.py` — `count_tokens()` function

**Suggested Fix:**
Add input guard at the top of `count_tokens()`:
```python
if not input_text or not input_text.strip():
    return 0
```

**Test Cases to Add:**
1. `test_count_tokens_empty_string` — assert `count_tokens("") == 0`
2. `test_count_tokens_whitespace_only` — assert `count_tokens("   ") == 0`
3. `test_count_tokens_none_input` — handle TypeError or return 0
================================================================================
```

### Advanced Usage

#### Different Repository

To analyze a different repository, update `.env`:

```env
GITHUB_REPO_OWNER=facebook
GITHUB_REPO_NAME=react
```

Then run commands as usual.

#### Debug Mode

For troubleshooting, enable debug logging:

```env
LOG_LEVEL=DEBUG
```

This will show:
- Tool invocations with parameters
- API request URLs (tokens are masked)
- Agent reasoning steps
- HTTP response codes

#### Output Redirection

Save report to a file:

```powershell
python src\main.py --report > issue_report_$(Get-Date -Format 'yyyy-MM-dd').md
```

---

## Deployment

### Local Development

Already configured by default. Just ensure:
1. Ollama is running: `ollama serve`
2. Model is downloaded: `ollama pull llama3.2:3b`
3. Environment variables are set in root `.env`

### CI/CD Integration (GitHub Actions)

Create `.github/workflows/issue-audit.yml`:

```yaml
name: Weekly Issue Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  audit-issues:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install uv
        run: pip install uv
      
      - name: Install dependencies
        run: |
          cd projects/04_github_issue_reporter
          uv venv .venv
          source .venv/bin/activate
          uv pip install -r requirements.txt
          uv pip install -e ../../common
      
      - name: Run issue report
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          GITHUB_REPO_OWNER: ${{ github.repository_owner }}
          GITHUB_REPO_NAME: ${{ github.event.repository.name }}
          OLLAMA_BASE_URL: ${{ secrets.OLLAMA_BASE_URL }}
          OLLAMA_API_KEY: ${{ secrets.OLLAMA_API_KEY }}
          OLLAMA_MODEL: llama3.2:3b
        run: |
          cd projects/04_github_issue_reporter
          source .venv/bin/activate
          python src/main.py --report > weekly_report.md
      
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: issue-report
          path: projects/04_github_issue_reporter/weekly_report.md
```

**Required Secrets:**
- `OLLAMA_BASE_URL`: Remote Ollama server URL
- `OLLAMA_API_KEY`: Remote Ollama Bearer token

### Docker Deployment

Create `Dockerfile` in project root:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY projects/04_github_issue_reporter/ /app/
COPY common/ /app/common/
COPY requirements-base.txt /app/

# Install dependencies
RUN uv venv .venv && \
    . .venv/bin/activate && \
    uv pip install -r requirements.txt && \
    uv pip install -e ./common

ENTRYPOINT [".venv/bin/python", "src/main.py"]
```

Build and run:

```bash
docker build -t github-issue-reporter .

docker run --rm \
  -e GITHUB_TOKEN=ghp_xxx \
  -e GITHUB_REPO_OWNER=youruser \
  -e GITHUB_REPO_NAME=yourrepo \
  -e OLLAMA_BASE_URL=http://host.docker.internal:11434 \
  -e OLLAMA_MODEL=llama3.2:3b \
  github-issue-reporter --report
```

---

## Testing

### Run Test Suite

```powershell
# Activate venv
.venv\Scripts\Activate.ps1

# Run all tests with coverage
pytest tests/ --cov=src --cov-report=term-missing --cov-fail-under=90 -v
```

### Test Coverage Report

```
---------- coverage: platform win32, python 3.11.x -----------
Name                  Stmts   Miss  Cover   Missing
---------------------------------------------------
src/__init__.py           0      0   100%
src/main.py             185      8    96%   42-45, 89
---------------------------------------------------
TOTAL                   185      8    96%
```

### Run Specific Test Classes

```powershell
# Test only tool functions
pytest tests/test_main.py::TestListOpenIssuesTool -v

# Test CLI argument parsing
pytest tests/test_main.py::TestCLIArgumentParsing -v

# Test error handling
pytest tests/test_main.py::TestErrorHandling -v
```

### Test Strategy

- **Unit tests:** Individual tool functions with mocked HTTP calls
- **Integration tests:** Agent invocation with mocked LLM and GitHub API
- **CLI tests:** Argument parsing and validation
- **Error handling tests:** Network errors, invalid inputs, missing config

**Key principle:** No real API calls in tests. All LLM and HTTP interactions are mocked.

---

## Troubleshooting

### Common Issues

#### Issue: `EnvironmentError: GITHUB_TOKEN not found`

**Cause:** Missing GitHub token in `.env` file.

**Solution:**
1. Create token at https://github.com/settings/tokens
2. Add to root `.env`: `GITHUB_TOKEN=ghp_your_token`
3. Verify: `python -c "from common.utils import require_env; require_env('GITHUB_TOKEN')"`

---

#### Issue: `GitHub API error: 404 - Not Found`

**Cause:** Repository doesn't exist or token lacks access.

**Solution:**
1. Verify repository exists: `https://github.com/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}`
2. Check token scopes (needs `repo` or `public_repo`)
3. For private repos, ensure token has `repo` scope

---

#### Issue: `GitHub API error: 403 - Forbidden` or `429 - Too Many Requests`

**Cause:** Rate limit exceeded or insufficient permissions.

**Solution:**
1. **Rate limiting:** Wait 1 hour or use authenticated token (5000 req/hr vs 60 req/hr)
2. **Permissions:** Regenerate token with correct scopes
3. Check rate limit status:
   ```powershell
   curl -H "Authorization: Bearer $GITHUB_TOKEN" https://api.github.com/rate_limit
   ```

---

#### Issue: `ModuleNotFoundError: No module named 'common'`

**Cause:** `ai-agent-common` package not installed in project venv.

**Solution:**
```powershell
cd projects\04_github_issue_reporter
.venv\Scripts\Activate.ps1
uv pip install -e ..\..\common
```

---

#### Issue: Agent produces generic/hallucinated recommendations

**Cause:** LLM not grounding responses in tool data.

**Solution:**
1. Verify tools are returning data (check logs with `LOG_LEVEL=DEBUG`)
2. Ensure issue has sufficient context (body + comments)
3. Try a larger/more capable model: `OLLAMA_MODEL=llama3.1:8b`

---

#### Issue: `Connection refused` to Ollama

**Cause:** Ollama server not running.

**Solution:**
```powershell
# Start Ollama
ollama serve

# Verify it's running
ollama list
```

---

### Debug Mode

Enable verbose logging for troubleshooting:

```env
LOG_LEVEL=DEBUG
```

This shows:
- Tool invocation parameters
- API request URLs (tokens masked)
- HTTP response status codes
- Agent reasoning steps
- Error stack traces

---

## Security Considerations

### Threat Model

| Threat | Mitigation |
|---|---|
| **Prompt Injection** | Content wrapped in XML delimiters; truncation; strict system prompt |
| **Token Leakage** | Tokens never logged; read via `require_env()`; gitignored `.env` |
| **Sensitive Data in Issues** | Bodies/comments not persisted; only passed to LLM |
| **Unbounded API Calls** | Pagination capped at 2 pages (200 issues); recursion limit set |
| **Rate Limiting** | Authenticated calls (5000 req/hr); handles 429 gracefully |

### Best Practices

✅ **DO:**
- Use tokens with minimum required scopes
- Rotate tokens regularly (90-day expiration recommended)
- Enable debug logging only when troubleshooting
- Review issue content before sharing LLM output externally

❌ **DON'T:**
- Commit `.env` files to version control
- Share tokens in chat/email
- Use `repo` scope for public-only access (use `public_repo`)
- Log full issue bodies or comments

---

## Performance & Limitations

### Performance Characteristics

| Metric | Value |
|---|---|
| **Report Mode (100 issues)** | ~5-10 seconds (2 API calls + LLM formatting) |
| **Recommendation Mode** | ~8-15 seconds (2-3 API calls + LLM reasoning) |
| **Max Issues Fetched** | 200 (2 pages × 100 per page) |
| **Issue Body Truncation** | 4000 characters |
| **Comment Truncation** | 1000 characters each, max 10 comments |
| **Agent Recursion Limit** | 10 iterations |

### Known Limitations

1. **Large Repositories:**
   - Only fetches first 200 open issues
   - For repos with > 200 issues, oldest issues may be missed
   - **Workaround:** Use GitHub filters before running (e.g., filter by label)

2. **Long Issue Threads:**
   - Only top 10 comments fetched
   - Each comment truncated to 1000 chars
   - **Workaround:** For critical issues, review full thread on GitHub

3. **LLM Context Window:**
   - Issue bodies truncated to 4000 chars
   - Very long issues lose tail content
   - **Workaround:** Use larger context models (e.g., `codellama:70b`)

4. **Language Support:**
   - LLM responses in English by default
   - Issue content in any language supported
   - **Workaround:** Modify system prompt for multilingual output

5. **No Write Operations:**
   - Agent is read-only (no issue creation, labeling, or commenting)
   - Intentional security constraint
   - **Workaround:** Manually apply recommendations

---

## Contributing

### Adding New Features

1. **New Tool:** Add `@tool` function in `src/main.py`
2. **Register Tool:** Add to `tools` list in `build_agent()`
3. **Test Tool:** Add test class in `tests/test_main.py`
4. **Update Docs:** Document in this README

### Reporting Issues

Use the GitHub issue tracker:
- **Bugs:** Use `bug` label, include error logs
- **Features:** Use `enhancement` label, describe use case
- **Questions:** Use `question` label

### Pull Request Guidelines

1. All changes must maintain >= 90% test coverage
2. Run tests before submitting: `pytest --cov --cov-fail-under=90`
3. Follow repository coding conventions (see [docs/contributing.md](../../docs/contributing.md))
4. Update README if behavior changes

---

## License

This project is part of the Agentic AI Development Framework.  
See root [LICENSE](../../LICENSE) file for details.

---

## Support & Resources

- **Documentation:** [docs/getting_started.md](../../docs/getting_started.md)
- **GitHub API Reference:** https://docs.github.com/en/rest
- **LangGraph Guide:** https://langchain-ai.github.io/langgraph/
- **Ollama Models:** https://ollama.com/library

---

**Built with ❤️ using LangChain, LangGraph, and Ollama**
