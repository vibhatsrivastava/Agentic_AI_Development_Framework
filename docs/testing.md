# Testing Conventions

> **Simplified, realistic testing standards for AI agent applications.**

---

## Overview

This repository follows a **pragmatic testing strategy** optimized for AI agent development:

- **75% coverage minimum** — realistic for mocked LLM testing
- **Focus on what matters** — tools, utilities, and critical logic paths
- **Mock all LLMs** — fast, deterministic, no API costs
- **Optional integration tests** — manual validation with real LLMs before deployment

### Testing Philosophy

**✅ Test thoroughly:**
- Tool functions (input validation, error handling, data formatting)
- Utility functions (logging, env loading, factories)
- Chain composition (LCEL piping, parameter passing)
- Error paths and edge cases

**⚠️ Test pragmatically:**
- Agent building (simple smoke tests — it's mostly LangGraph code)
- LLM factory calls (basic instantiation checks)
- Complex agent workflows (mock minimally, test manually)

**❌ Don't over-test:**
- Mocking complex LangGraph internals
- Testing LangChain library code
- Excessive assertion on implementation details

---

## Quick Start

### Running Tests

```powershell
# Activate virtual environment
.venv\Scripts\Activate.ps1

# Run all tests (fast, mocked)
pytest

# Run tests with coverage report
pytest --cov --cov-report=term-missing

# Run tests for specific module
pytest common/tests/test_llm_factory.py -v

# Run only unit tests (fastest)
pytest -m unit

# Skip integration tests (CI-friendly)
pytest -m "not integration"

# Run integration tests (manual, requires real Ollama)
pytest -m integration

# Run with coverage check (fails if < 75%)
pytest --cov --cov-fail-under=75
```

### Test File Structure

```
common/
├── llm_factory.py              # Production code
└── tests/
    ├── conftest.py             # Shared fixtures
    ├── test_llm_factory.py     # Tests for llm_factory.py
    └── test_utils.py           # Tests for utils.py

projects/01_hello_langchain/
├── src/
│   └── main.py                 # Production code
└── tests/
    ├── conftest.py             # Project-specific fixtures
    └── test_main.py            # Tests for main.py
```

Place tests in a `tests/` directory parallel to the code being tested.

---

## Testing Framework

### Pytest Configuration

The repository uses pytest with these key configurations (defined in `pytest.ini`):

- **Minimum coverage**: 75% globally, enforced via `--cov-fail-under=75`
- **Test discovery**: `test_*.py` and `*_test.py` files in `common/` and `projects/`
- **Coverage reports**: Terminal output (with missing lines) + HTML report in `htmlcov/`
- **Test markers**: `unit` (fast mocked tests), `integration` (real LLM tests), `smoke` (critical paths)

### Required Dependencies

Defined in `requirements-base.txt`:

```
pytest>=8.0.0             # Testing framework
pytest-cov>=4.1.0         # Coverage plugin
pytest-mock>=3.12.0       # Mocking utilities
pytest-asyncio>=0.23.0    # Async test support
responses>=0.24.0         # HTTP mocking
```

---

## Test Types

### Unit Tests

**Purpose**: Test individual functions/classes in isolation with all dependencies mocked.

**Characteristics**:
- Fast (< 100ms per test)
- No external calls (LLM, APIs, files)
- Deterministic (same result every run)
- High coverage of logic branches

**Example**:

```python
import pytest
from common.utils import get_logger, require_env

class TestGetLogger:
    """Unit tests for get_logger()."""
    
    def test_returns_logger_instance(self):
        """get_logger() returns a logging.Logger instance."""
        logger = get_logger("test")
        assert logger is not None
        assert logger.name == "test"
    
    def test_respects_log_level_env_var(self, monkeypatch):
        """Logger level is set from LOG_LEVEL env var."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        logger = get_logger("test")
        assert logger.level == 10  # logging.DEBUG

class TestRequireEnv:
    """Unit tests for require_env()."""
    
    def test_returns_value_when_set(self, monkeypatch):
        """require_env() returns value when env var is set."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        assert require_env("TEST_VAR") == "test_value"
    
    def test_raises_error_when_missing(self):
        """require_env() raises EnvironmentError when var is unset."""
        with pytest.raises(EnvironmentError, match="TEST_MISSING"):
            require_env("TEST_MISSING")
```

**Markers**: Mark unit tests with `@pytest.mark.unit` for selective execution.

---

### Integration Tests

**Purpose**: Test interactions between multiple components (chains, agents, tools).

**Two Types:**

**1. Mocked Integration Tests** (default, run in CI):
- Test complete workflows with mocked LLMs
- Verify component integration
- Fast and deterministic

**2. Real LLM Integration Tests** (manual, before PR merge):
- Test with actual Ollama server
- Validate prompt engineering
- Verify real agent behavior

**Mocked Integration Example**:

```python
import pytest
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from common.llm_factory import get_llm

@pytest.mark.integration
class TestLCELChain:
    """Integration tests for LCEL chain execution (mocked)."""
    
    def test_prompt_llm_parser_chain(self, mock_llm):
        """Test complete chain: prompt | llm | parser."""
        # Arrange
        mock_llm.invoke.return_value = "Mocked AI response"
        prompt = PromptTemplate.from_template("Q: {question}\nA:")
        chain = prompt | mock_llm | StrOutputParser()
        
        # Act
        result = chain.invoke({"question": "What is AI?"})
        
        # Assert
        assert result == "Mocked AI response"
        mock_llm.invoke.assert_called_once()
```

**Real LLM Integration Example** (run manually):

```python
import pytest
from src.main import build_agent, ask

@pytest.mark.integration
class TestAgentWithRealLLM:
    """Integration tests with real Ollama (skip in CI)."""
    
    @pytest.mark.skip(reason="Requires running Ollama server")
    def test_weather_agent_real_llm(self):
        """Smoke test with actual Ollama — run manually before PR merge."""
        agent = build_agent()  # Uses real ChatOllama
        result = ask(agent, "What's the weather in London?")
        
        # Basic validation — just verify it runs
        assert len(result) > 0
        assert "London" in result or "weather" in result.lower()
```

**Running Integration Tests:**

```powershell
# Skip integration tests (CI mode)
pytest -m "not integration"

# Run only integration tests (manual validation)
pytest -m integration

# Run real LLM tests (requires Ollama running)
pytest -m integration --run-integration-real
```

---

### Mocking LLM Calls

**Critical Rule**: **Never make real LLM API calls in tests**. Always mock Ollama/LLM interactions.

#### Why Mock LLMs?

- **Speed**: Real LLM calls take seconds; mocked calls take microseconds
- **Cost**: Avoid unnecessary API usage (especially for remote servers)
- **Determinism**: LLM responses vary; mocked responses are consistent
- **Test isolation**: Tests shouldn't depend on external service availability

#### Mocking Patterns

**Pattern 1: Mock at the factory level** (recommended)

```python
# In conftest.py
import pytest
from unittest.mock import Mock

@pytest.fixture
def mock_llm(monkeypatch):
    """Mock OllamaLLM for string-based chains."""
    mock = Mock()
    mock.invoke.return_value = "Mocked response"
    monkeypatch.setattr("langchain_ollama.OllamaLLM", lambda **kwargs: mock)
    return mock

@pytest.fixture
def mock_chat_llm(monkeypatch):
    """Mock ChatOllama for agentic workflows."""
    mock = Mock()
    from langchain_core.messages import AIMessage
    mock.invoke.return_value = AIMessage(content="Mocked chat response")
    monkeypatch.setattr("langchain_ollama.ChatOllama", lambda **kwargs: mock)
    return mock

@pytest.fixture
def mock_embeddings(monkeypatch):
    """Mock OllamaEmbeddings for RAG pipelines."""
    mock = Mock()
    mock.embed_documents.return_value = [[0.1] * 768 for _ in range(3)]
    mock.embed_query.return_value = [0.1] * 768
    monkeypatch.setattr("langchain_ollama.OllamaEmbeddings", lambda **kwargs: mock)
    return mock
```

**Pattern 2: Mock specific LLM responses**

```python
def test_chain_with_specific_response(mock_llm):
    """Test chain behavior with a specific mocked LLM response."""
    mock_llm.invoke.return_value = "The capital of France is Paris."
    
    chain = prompt | mock_llm | StrOutputParser()
    result = chain.invoke({"question": "What is the capital of France?"})
    
    assert "Paris" in result
```

**Pattern 3: Mock tool-calling agents**

```python
def test_agent_tool_execution(mock_chat_llm):
    """Test ReAct agent with mocked tool calls."""
    from langgraph.prebuilt import create_react_agent
    from langchain_core.tools import tool
    from langchain_core.messages import AIMessage, ToolMessage
    
    @tool
    def calculator(expression: str) -> str:
        """Evaluate a math expression."""
        return str(eval(expression))
    
    # Mock agent to call tool, then return final answer
    mock_chat_llm.invoke.side_effect = [
        AIMessage(content="", tool_calls=[{"name": "calculator", "args": {"expression": "2+2"}, "id": "1"}]),
        AIMessage(content="The answer is 4")
    ]
    
    agent = create_react_agent(model=mock_chat_llm, tools=[calculator])
    result = agent.invoke({"messages": [{"role": "user", "content": "What is 2+2?"}]})
    
    assert "4" in result["messages"][-1].content
```

---

## Test Organization

### File Naming

- **Production file**: `src/agent.py` → **Test file**: `tests/test_agent.py`
- **Production file**: `common/utils.py` → **Test file**: `common/tests/test_utils.py`

### Test Class Naming

Group related tests into classes:

```python
class TestFunctionName:
    """Tests for function_name()."""
    
    def test_basic_case(self):
        """Test normal operation."""
        pass
    
    def test_edge_case_empty_input(self):
        """Test with empty input."""
        pass
    
    def test_error_case_invalid_type(self):
        """Test error handling."""
        pass
```

### Test Method Naming

Use descriptive names that explain what is tested:

✅ **Good**:
- `test_returns_logger_with_correct_name()`
- `test_raises_error_when_env_var_missing()`
- `test_chain_executes_with_mocked_llm()`

❌ **Bad**:
- `test_1()`
- `test_logger()`
- `test_error()`

### Docstrings

Every test function should have a docstring explaining what it tests:

```python
def test_require_env_raises_error_when_missing(self):
    """require_env() raises EnvironmentError when env var is not set."""
    with pytest.raises(EnvironmentError):
        require_env("NONEXISTENT_VAR")
```

---

## Coverage Requirements

### Minimum Thresholds

- **Global**: 75% coverage across all production code (realistic for mocked AI testing)
- **Critical modules** (`common/` utilities, tools): Aim for 85%+
- **Agent logic**: Focus on tools and error handling, not LangGraph internals

**Why 75%?**

AI agent testing with mocked LLMs has inherent limitations:
- **Mocked LLMs don't validate prompts** — 100% coverage doesn't test if prompts work
- **Agent orchestration is LangGraph code** — testing library internals adds little value
- **Real validation happens manually** — integration tests with real Ollama before deployment

75% ensures **critical paths are tested** without forcing you to mock complex LangGraph internals.

### What to Test

✅ **Must test**:
- All public functions and methods
- All conditional branches (`if`, `else`, `elif`, `match`)
- Exception handlers (`try`/`except` blocks)
- Environment variable handling
- Input validation logic
- Edge cases (empty, None, invalid types)

✅ **Test with mocks**:
- All LLM/Ollama calls
- External API requests
- File I/O operations
- Database queries

❌ **May skip**:
- Private helper functions if fully covered by public API tests
- Simple property getters/setters with no logic
- Generated code (e.g., dataclasses, Pydantic models)

### Checking Coverage

```powershell
# Full coverage report
pytest --cov --cov-report=term-missing

# Coverage for specific module
pytest tests/test_utils.py --cov=common.utils --cov-report=term-missing

# Fail if coverage < 75%
pytest --cov --cov-fail-under=75

# Generate HTML report (viewable in browser)
pytest --cov --cov-report=html
# Open htmlcov/index.html to see detailed line-by-line coverage
```

### Filling Coverage Gaps

If coverage < 75%, identify uncovered lines:

```
---------- coverage: platform win32, python 3.13.5 -----------
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
common\utils.py         20      6    70%   45-46, 52-54
--------------------------------------------------
TOTAL                   20      6    70%
```

**Prioritize covering:**
1. **Error handling paths** (exceptions, validation)
2. **Tool functions** (critical for agent correctness)
3. **Utility functions** (reused across projects)

**Don't force coverage for:**
- Simple agent builders that just call `create_react_agent`
- LangGraph graph construction (it's library code)
- Trivial property accessors

---

## Shared Fixtures

### conftest.py

Place shared fixtures in `conftest.py` files:

**common/tests/conftest.py** (shared across all tests):

```python
"""
Shared pytest fixtures for all tests in the repository.
"""

import pytest
from unittest.mock import Mock
from langchain_core.messages import AIMessage

@pytest.fixture
def mock_llm(monkeypatch):
    """
    Mock OllamaLLM for testing string-based chains.
    
    Usage:
        def test_my_chain(mock_llm):
            mock_llm.invoke.return_value = "Test response"
            chain = prompt | mock_llm | StrOutputParser()
            assert chain.invoke({}) == "Test response"
    """
    mock = Mock()
    mock.invoke.return_value = "Mocked LLM response"
    monkeypatch.setattr("langchain_ollama.OllamaLLM", lambda **kwargs: mock)
    return mock

@pytest.fixture
def mock_chat_llm(monkeypatch):
    """
    Mock ChatOllama for testing agentic workflows.
    
    Usage:
        def test_my_agent(mock_chat_llm):
            mock_chat_llm.invoke.return_value = AIMessage(content="Test")
            # ... test agent logic
    """
    mock = Mock()
    mock.invoke.return_value = AIMessage(content="Mocked chat response")
    monkeypatch.setattr("langchain_ollama.ChatOllama", lambda **kwargs: mock)
    return mock

@pytest.fixture
def mock_embeddings(monkeypatch):
    """
    Mock OllamaEmbeddings for testing RAG pipelines.
    
    Usage:
        def test_my_rag(mock_embeddings):
            vectorstore = FAISS.from_documents(docs, mock_embeddings)
            # ... test retrieval
    """
    mock = Mock()
    mock.embed_documents.return_value = [[0.1] * 768]
    mock.embed_query.return_value = [0.1] * 768
    monkeypatch.setattr("langchain_ollama.OllamaEmbeddings", lambda **kwargs: mock)
    return mock

@pytest.fixture
def mock_env(monkeypatch):
    """
    Set common environment variables for tests.
    
    Usage:
        def test_with_env(mock_env):
            # OLLAMA_BASE_URL and other vars are already set
            llm = get_llm()
    """
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://test:11434")
    monkeypatch.setenv("OLLAMA_MODEL", "test-model")
    monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "test-embed-model")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
```

**projects/01_hello_langchain/tests/conftest.py** (project-specific):

```python
"""
Project-specific fixtures for 01_hello_langchain tests.
"""

import pytest

@pytest.fixture
def sample_question():
    """Return a sample question for testing the main chain."""
    return "What is LangChain?"

@pytest.fixture
def expected_keywords():
    """Return keywords expected in LLM responses."""
    return ["LangChain", "framework", "AI", "agents"]
```

---

## Example Test Files

### Example 1: Testing Utility Functions

**common/tests/test_utils.py**:

```python
"""
test_utils.py — Comprehensive tests for common/utils.py

Coverage target: >= 90%
"""

import pytest
import logging
from common.utils import get_logger, require_env


class TestGetLogger:
    """Unit tests for get_logger()."""
    
    def test_returns_logger_instance(self):
        """get_logger() returns a logging.Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_respects_log_level_from_env(self, monkeypatch):
        """Logger uses LOG_LEVEL env var to set level."""
        monkeypatch.setenv("LOG_LEVEL", "DEBUG")
        logger = get_logger("test")
        assert logger.level == logging.DEBUG
    
    def test_defaults_to_info_level(self, monkeypatch):
        """Logger defaults to INFO when LOG_LEVEL is not set."""
        monkeypatch.delenv("LOG_LEVEL", raising=False)
        logger = get_logger("test")
        assert logger.level == logging.INFO


class TestRequireEnv:
    """Unit tests for require_env()."""
    
    def test_returns_value_when_set(self, monkeypatch):
        """require_env() returns the env var value when set."""
        monkeypatch.setenv("TEST_VAR", "test_value")
        result = require_env("TEST_VAR")
        assert result == "test_value"
    
    def test_raises_error_when_missing(self):
        """require_env() raises EnvironmentError when var is missing."""
        with pytest.raises(EnvironmentError, match="MISSING_VAR"):
            require_env("MISSING_VAR")
    
    def test_raises_error_when_empty(self, monkeypatch):
        """require_env() raises EnvironmentError when var is empty string."""
        monkeypatch.setenv("EMPTY_VAR", "")
        with pytest.raises(EnvironmentError, match="EMPTY_VAR"):
            require_env("EMPTY_VAR")
    
    def test_error_message_mentions_env_example(self):
        """Error message guides user to .env.example."""
        with pytest.raises(EnvironmentError, match=".env.example"):
            require_env("MISSING_VAR")
```

### Example 2: Testing LLM Factory

**common/tests/test_llm_factory.py**:

```python
"""
test_llm_factory.py — Tests for common/llm_factory.py

Tests cover:
- get_llm() returns configured OllamaLLM
- get_chat_llm() returns configured ChatOllama
- get_embeddings() returns configured OllamaEmbeddings
- Model and parameter overrides work correctly
- Auth headers are set when API key is present

Coverage target: >= 90%
"""

import pytest
from unittest.mock import patch, Mock
from common.llm_factory import get_llm, get_chat_llm, get_embeddings


@pytest.mark.unit
class TestGetLLM:
    """Unit tests for get_llm()."""
    
    @patch("common.llm_factory.OllamaLLM")
    def test_returns_ollama_llm_instance(self, mock_class):
        """get_llm() returns an OllamaLLM instance."""
        llm = get_llm()
        mock_class.assert_called_once()
        assert llm is not None
    
    @patch("common.llm_factory.OllamaLLM")
    def test_uses_default_model_from_env(self, mock_class, monkeypatch):
        """get_llm() uses OLLAMA_MODEL from environment."""
        monkeypatch.setenv("OLLAMA_MODEL", "test-model:latest")
        get_llm()
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "test-model:latest"
    
    @patch("common.llm_factory.OllamaLLM")
    def test_model_override_works(self, mock_class):
        """get_llm(model='custom') overrides default model."""
        get_llm(model="custom-model")
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "custom-model"
    
    @patch("common.llm_factory.OllamaLLM")
    def test_temperature_parameter(self, mock_class):
        """get_llm(temperature=0.7) sets temperature."""
        get_llm(temperature=0.7)
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["temperature"] == 0.7


@pytest.mark.unit
class TestGetChatLLM:
    """Unit tests for get_chat_llm()."""
    
    @patch("common.llm_factory.ChatOllama")
    def test_returns_chat_ollama_instance(self, mock_class):
        """get_chat_llm() returns a ChatOllama instance."""
        chat = get_chat_llm()
        mock_class.assert_called_once()
        assert chat is not None
    
    @patch("common.llm_factory.ChatOllama")
    def test_json_format_mode(self, mock_class):
        """get_chat_llm(format='json') enables JSON output mode."""
        get_chat_llm(format="json")
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["format"] == "json"
    
    @patch("common.llm_factory.ChatOllama")
    def test_num_ctx_parameter(self, mock_class):
        """get_chat_llm(num_ctx=8192) sets context window size."""
        get_chat_llm(num_ctx=8192)
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["num_ctx"] == 8192


@pytest.mark.unit
class TestGetEmbeddings:
    """Unit tests for get_embeddings()."""
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_returns_embeddings_instance(self, mock_class):
        """get_embeddings() returns an OllamaEmbeddings instance."""
        embeddings = get_embeddings()
        mock_class.assert_called_once()
        assert embeddings is not None
    
    @patch("common.llm_factory.OllamaEmbeddings")
    def test_uses_default_embedding_model(self, mock_class, monkeypatch):
        """get_embeddings() uses OLLAMA_EMBEDDING_MODEL from env."""
        monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "test-embed-model")
        get_embeddings()
        call_kwargs = mock_class.call_args[1]
        assert call_kwargs["model"] == "test-embed-model"
```

### Example 3: Testing a Complete Chain

**projects/01_hello_langchain/tests/test_main.py**:

```python
"""
test_main.py — Integration tests for 01_hello_langchain/src/main.py

Tests cover:
- Chain initialization and execution
- Prompt formatting
- Output parsing
- Mocked LLM interactions

Coverage target: >= 90%
"""

import pytest
import sys
import os

# Allow imports from common/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


@pytest.mark.integration
class TestMainChain:
    """Integration tests for the main Q&A chain."""
    
    def test_chain_executes_successfully(self, mock_llm):
        """Test that the chain runs end-to-end with mocked LLM."""
        # Arrange
        mock_llm.invoke.return_value = "LangChain is a framework for AI agents."
        
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        chain = prompt | mock_llm | StrOutputParser()
        
        # Act
        result = chain.invoke({"question": "What is LangChain?"})
        
        # Assert
        assert isinstance(result, str)
        assert len(result) > 0
        assert "LangChain" in result
    
    def test_prompt_formats_correctly(self):
        """Test that the prompt template formats input correctly."""
        prompt = PromptTemplate.from_template(
            "Answer the following question in 2-3 sentences.\n\nQuestion: {question}\n\nAnswer:"
        )
        formatted = prompt.format(question="What is AI?")
        
        assert "What is AI?" in formatted
        assert "Answer:" in formatted
    
    def test_chain_handles_various_questions(self, mock_llm):
        """Test chain with multiple different questions."""
        mock_llm.invoke.return_value = "Test answer"
        
        prompt = PromptTemplate.from_template("Q: {question}\nA:")
        chain = prompt | mock_llm | StrOutputParser()
        
        questions = [
            "What is Python?",
            "Explain machine learning",
            "What are LLMs?"
        ]
        
        for q in questions:
            result = chain.invoke({"question": q})
            assert result == "Test answer"
        
        assert mock_llm.invoke.call_count == 3
```

---

## Best Practices

### Do's ✅

- **Write tests first** (TDD) or **immediately after** implementing a feature
- **Mock all external dependencies** (LLMs, APIs, databases, files)
- **Use descriptive test names** that explain what is tested
- **Test edge cases** (empty inputs, None, invalid types, boundary values)
- **Test error paths** (exceptions, validation failures)
- **Use fixtures** for common setup to avoid duplication
- **Keep tests fast** (< 1 second for unit tests, < 5 seconds for integration tests)
- **Run tests before committing** code
- **Check coverage** regularly and fill gaps immediately

### Don'ts ❌

- **Don't make real LLM calls** in tests (always mock)
- **Don't skip tests** because "it's too simple to test"
- **Don't test implementation details** (test behavior, not internals)
- **Don't share state** between tests (each test should be isolated)
- **Don't commit code** with < 90% coverage
- **Don't ignore flaky tests** (fix or remove them)
- **Don't hardcode paths** (use `tmp_path` fixture for file tests)

---

## CI/CD Integration

Tests run automatically in GitHub Actions on every push and PR.

**Workflow**: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [main, dev]
  pull_request:
    branches: [main, dev]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install uv
        uses: astral-sh/setup-uv@v5
      - name: Install dependencies
        run: |
          uv pip install -r requirements-base.txt
          uv pip install -e ./common
      - name: Run tests with coverage
        run: |
          pytest --cov --cov-report=term --cov-report=html --cov-fail-under=90
      - name: Upload coverage report
        uses: actions/upload-artifact@v4
        with:
          name: coverage-report
          path: htmlcov/
```

The pipeline **fails if coverage < 90%**, preventing untested code from being merged.

---

## Troubleshooting

### Tests Not Discovered

**Problem**: `pytest` finds no tests.

**Solution**: Ensure test files match naming patterns:
- `test_*.py` or `*_test.py`
- Test functions start with `test_`
- Test classes start with `Test`

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'common'`

**Solution**: Add `sys.path.insert` at the top of test files:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))
```

### Coverage Not Measured

**Problem**: Coverage is 0% or not displayed.

**Solution**: Ensure `pytest.ini` exists with coverage configuration, and run:

```powershell
pytest --cov=<module> --cov-report=term
```

### Flaky Tests

**Problem**: Tests pass sometimes and fail other times.

**Solution**:
- Check for shared state between tests (use fixtures, not globals)
- Ensure all external calls are mocked
- Check for race conditions in async tests
- Use `pytest-randomly` to catch order-dependent failures

---

## Using the Test Agent

To automatically generate tests with >= 90% coverage:

```
@test-agent generate tests for common/llm_factory.py
```

The agent will:
1. Analyze the code
2. Generate comprehensive test file
3. Run tests and verify coverage
4. Report results

See [.github/test-agent.agent.md](.github/test-agent.agent.md) for details.

---

## References

- **pytest documentation**: https://docs.pytest.org/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **LangChain testing guide**: https://python.langchain.com/docs/contributing/testing
- **Repository conventions**: [.github/copilot-instructions.md](.github/copilot-instructions.md)
- **Test agent**: [.github/test-agent.agent.md](.github/test-agent.agent.md)

---

## Summary

- **Minimum coverage**: 90% for all production code
- **Framework**: pytest with pytest-cov, pytest-mock
- **Mock all LLMs**: Never make real API calls in tests
- **Test types**: Unit (isolated), Integration (multi-component), Mocked (LLM interactions)
- **Run before commit**: `pytest --cov --cov-fail-under=90`
- **Use test agent**: `@test-agent` to auto-generate tests

**Every new feature must include tests. Every bug fix must include a regression test. Coverage is non-negotiable.**
