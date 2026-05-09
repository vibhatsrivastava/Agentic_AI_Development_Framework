# Simplified Testing Strategy

> **Pragmatic testing approach for AI agent development**

---

## The Problem with Traditional Testing

AI agent applications are fundamentally different from traditional software:

- **Mocked LLMs don't validate behavior** — 100% coverage with mocks doesn't test if your prompts work
- **LLM responses vary** — deterministic testing is impossible with real models
- **Library code dominates** — Most agent code is LangGraph/LangChain library calls
- **Real validation is manual** — You need to test with actual LLMs before deployment

**Traditional approach:**
```
Write code → Mock everything → 90% coverage → Ship
❌ Problem: Tests pass, but agent doesn't work in production
```

**Our approach:**
```
Write code → Mock critical paths → 75% coverage → Manual validation → Ship
✅ Reality: Tests verify logic, manual testing validates behavior
```

---

## Three-Tier Testing Strategy

```
┌──────────────────────────────────────────────┐
│ Tier 1: Unit Tests (Automated, Fast)        │
│ • Tools, utilities, validation logic        │
│ • Mocked LLMs, mocked APIs                   │
│ • Target: 75% coverage minimum               │
│ • Run on every commit (CI)                   │
├──────────────────────────────────────────────┤
│ Tier 2: Integration Tests (Automated, Mock) │
│ • Chain composition, error handling          │
│ • Mocked LLM responses                       │
│ • Verify components work together            │
│ • Run on every commit (CI)                   │
├──────────────────────────────────────────────┤
│ Tier 3: Manual Validation (Real LLMs)       │
│ • Test with actual Ollama                    │
│ • Verify prompts, tool calling, outputs      │
│ • Run before PR merge                        │
│ • Not automated (too slow, non-deterministic)│
└──────────────────────────────────────────────┘
```

---

## What to Test (and What Not to Test)

### ✅ Test Thoroughly with Mocks

**1. Tool Functions**
```python
# High value — tools are critical to agent correctness
@tool
def get_weather(city: str) -> str:
    """Get weather for a city."""
    if not city:
        raise ValueError("City required")  # ✅ Test this
    response = requests.get(f"api/weather?city={city}")  # ✅ Mock this
    return parse_response(response)  # ✅ Test this
```

**Test coverage target: 90%+** — Tools are the agent's interface to the world.

**2. Utilities**
```python
# High value — reused across all projects
def get_logger(name: str) -> Logger:
    level = os.getenv("LOG_LEVEL", "INFO")  # ✅ Test with different levels
    logger = logging.getLogger(name)  # ✅ Test returns correct instance
    return logger
```

**Test coverage target: 85%+** — Utilities underpin everything.

**3. Input Validation & Error Handling**
```python
# High value — prevents runtime failures
def validate_config(config: dict) -> None:
    if "api_key" not in config:  # ✅ Test missing key
        raise ConfigError("API key required")
    if not isinstance(config["timeout"], int):  # ✅ Test wrong type
        raise ConfigError("Timeout must be int")
```

**Test coverage target: 100%** — Error paths must be tested.

---

### ⚠️ Test Pragmatically (Smoke Tests)

**1. Agent Builders**
```python
# Low value to over-test — it's mostly LangGraph library code
def build_agent():
    llm = get_chat_llm()  # ✅ Mock this
    return create_react_agent(  # ⚠️ Don't mock LangGraph internals
        model=llm,
        tools=[get_weather]
    )

# Simple smoke test is enough
def test_build_agent(mock_chat_llm):
    """Agent builds without errors."""
    agent = build_agent()
    assert agent is not None  # ✅ Basic validation
    # Don't: assert mock_chat_llm.called_with(...) ❌ Over-testing
```

**Test coverage target: 50-60%** — Just verify it doesn't crash.

**2. LLM Factory Calls**
```python
# Low value to over-test — simple wrappers
def get_chat_llm(model: str = None):
    return ChatOllama(
        base_url=os.getenv("OLLAMA_BASE_URL"),
        model=model or os.getenv("OLLAMA_MODEL")
    )

# Basic test is sufficient
def test_get_chat_llm(monkeypatch):
    """Factory returns ChatOllama instance."""
    llm = get_chat_llm()
    assert llm is not None  # ✅ Smoke test
    # Don't: Test every parameter ❌ Over-testing
```

**Test coverage target: 60-70%** — Verify basic instantiation.

---

### ❌ Don't Test (Low Value)

**1. LangChain/LangGraph Library Code**
```python
# Don't test library internals
def test_langraph_create_react_agent():  # ❌ Don't do this
    """Test LangGraph's create_react_agent function."""
    # This is testing the library, not your code
    pass
```

**2. Simple Property Accessors**
```python
@dataclass
class Config:
    api_key: str
    timeout: int

# Don't test trivial getters
def test_config_api_key():  # ❌ Don't do this
    config = Config(api_key="test", timeout=30)
    assert config.api_key == "test"  # Wastes time
```

**3. Mocking Complex Agent Workflows**
```python
# Don't mock entire agent execution flows
def test_agent_full_execution_mocked():  # ❌ Don't do this
    """Test agent with mocked tool calls, messages, etc."""
    # This creates brittle tests that break when LangGraph changes
    # Test this manually with real Ollama instead
    pass
```

---

## Pre-PR Checklist

Before merging any PR, complete this checklist:

### Automated Tests (Must Pass)

```powershell
# 1. Run all unit tests
pytest -m unit -v
# ✅ All tests should pass

# 2. Check coverage
pytest --cov --cov-fail-under=75
# ✅ Coverage should be >= 75%

# 3. Run integration tests
pytest -m integration -v
# ✅ All mocked integration tests should pass
```

### Manual Validation (Required)

```powershell
# 4. Test with real Ollama (manual)
# Start Ollama: ollama serve
# Run the agent manually:
cd projects/03_weather_reporting_agent
python src/main.py
# ✅ Verify agent responds correctly
# ✅ Check tool calls work
# ✅ Validate output format
```

**What to verify:**
- Agent understands the prompt
- Tools are called with correct arguments
- Error handling works (try invalid inputs)
- Output format is correct

### Code Quality

```powershell
# 5. Check for obvious issues
pytest --tb=short
# ✅ No import errors
# ✅ No syntax errors
```

---

## CI/CD Pipeline Strategy

### GitHub Actions (Automated)

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      
      - name: Install dependencies
        run: |
          pip install uv
          uv venv
          uv pip install -r requirements-base.txt
          uv pip install -e ./common
      
      - name: Run unit tests
        run: pytest -m "not integration" --cov --cov-fail-under=75
      
      # ✅ Fast (< 1 minute)
      # ✅ No real LLM calls
      # ✅ Verifies critical logic
```

### Manual Testing (Pre-Merge)

**Required before every PR merge:**

1. Start Ollama locally: `ollama serve`
2. Run the agent manually: `python src/main.py`
3. Test 3-5 realistic scenarios
4. Verify outputs are correct

**Time investment: 2-5 minutes per PR**

---

## Example: Testing a New Agent

### Scenario: Weather Reporting Agent

**File structure:**
```
projects/03_weather_reporting_agent/
├── src/
│   └── main.py          # Agent code
└── tests/
    ├── conftest.py      # Fixtures
    └── test_weather_agent.py  # Tests
```

### Step 1: Write Tool Tests (High Priority)

```python
# tests/test_weather_agent.py
import pytest
import responses
from src.main import get_weather

class TestGetWeatherTool:
    """Test the get_weather tool function."""
    
    @responses.activate
    def test_valid_city_returns_weather(self):
        """get_weather returns formatted weather for valid city."""
        # Mock geocoding API
        responses.add(
            responses.GET,
            "https://geocoding-api.open-meteo.com/v1/search",
            json={"results": [{"latitude": 51.5, "longitude": -0.1}]}
        )
        # Mock weather API
        responses.add(
            responses.GET,
            "https://api.open-meteo.com/v1/forecast",
            json={"current": {"temperature_2m": 15.0, "wind_speed_10m": 10.0}}
        )
        
        result = get_weather("London")
        
        assert "15.0°C" in result
        assert "10.0 km/h" in result
    
    def test_invalid_city_returns_error_message(self):
        """get_weather returns error for unknown city."""
        result = get_weather("NonexistentCity123")
        assert "not found" in result.lower()
```

**Time: 15-20 minutes** | **Value: Very High** ✅

### Step 2: Write Smoke Tests (Low Priority)

```python
class TestBuildAgent:
    """Smoke test for agent building."""
    
    def test_agent_builds_successfully(self, mock_chat_llm):
        """build_agent() returns agent without errors."""
        from src.main import build_agent
        
        agent = build_agent()
        assert agent is not None
```

**Time: 2-3 minutes** | **Value: Medium** ⚠️

### Step 3: Manual Validation (Required)

```powershell
# Start Ollama
ollama serve

# Run agent
python src/main.py

# Test cases:
# 1. "What's the weather in London?"
# 2. "Tell me the weather in Tokyo"
# 3. "Is it raining in NonexistentCity123?"  # Error case
```

**Time: 5 minutes** | **Value: Very High** ✅

### Result

- **Test coverage**: ~75% (tools well-tested, agent minimally tested)
- **Time investment**: ~25 minutes total
- **Confidence**: High (critical paths verified, manual validation done)

---

## Summary

### Key Principles

1. **75% coverage is realistic** — Higher doesn't add value for mocked AI tests
2. **Test what you write** — Tools, utilities, validation logic
3. **Don't test libraries** — LangChain/LangGraph are already tested
4. **Validate manually** — Real LLMs before deployment
5. **Keep tests fast** — CI should finish in < 2 minutes

### Time Allocation

Per new agent/feature:
- **Writing tests**: 20-30 minutes
- **Manual validation**: 5-10 minutes
- **Total**: 25-40 minutes

This is **sustainable** and provides **real confidence** that your code works.

### Remember

> "Tests don't prove correctness — they prove logic integrity. Manual validation proves behavior correctness."

Mocked tests verify your code doesn't crash. Real LLM testing verifies it actually works. **Do both.**
