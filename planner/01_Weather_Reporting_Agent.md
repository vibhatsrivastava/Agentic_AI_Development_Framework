# 01 — Weather Reporting Agent

> **Difficulty:** Beginner | **Pattern:** ReAct Agent with Tool Use  
> **LangChain Components Used:** `ChatOllama`, `@tool`, `create_agent` (LangChain), `BaseModel` (Pydantic), `argparse`

---

## Table of Contents

1. [Use Case Description / Scenario](#1-use-case-description--scenario)
2. [Objective](#2-objective)
3. [Step-by-Step Thought Process](#3-step-by-step-thought-process)
4. [Pseudo Code](#4-pseudo-code)
5. [High Level Workflow Diagram](#5-high-level-workflow-diagram)
6. [Low Level Workflow Diagram](#6-low-level-workflow-diagram)
7. [Implementation Steps](#7-implementation-steps)
8. [Code Snippets](#8-code-snippets)
9. [Test Cases](#9-test-cases)
10. [Expected Outcomes](#10-expected-outcomes)

---

## 1. Use Case Description / Scenario

A user wants to ask a conversational AI assistant for the **current weather of any city** by typing a natural language question such as:

- _"What is the weather like in Tokyo today?"_
- _"Tell me the temperature in London right now."_
- _"Is it raining in Sydney?"_

The assistant must:
1. **Understand** the intent from the natural language input
2. **Identify** the city name
3. **Call** a weather tool to fetch real data
4. **Respond** in natural language with the weather information

This is a classic **tool-using agent** use case — the LLM cannot know real-time weather from training data alone, so it must call an external tool to get the answer.

---

## 2. Objective

| Item | Detail |
|---|---|
| **Primary Goal** | Build a ReAct agent that answers weather questions for any city using a live weather API |
| **Agent Type** | Single-agent with one tool |
| **Reasoning Pattern** | ReAct (Thought → Action → Observation → Final Answer) |
| **LLM Used** | `ChatOllama` via `get_chat_llm()` |
| **Tool** | `get_weather(city)` — calls the Open-Meteo API (free, no API key needed) |
| **Input** | Natural language question — via CLI argument, interactive prompt, or default demo |
| **Output** | Structured `WeatherReport` (Pydantic) rendered as a natural language weather report |
| **Anti-hallucination** | System prompt (verbatim quoting rules) + structured output (`response_format=WeatherReport`) |

### Why This Is a Good First Agent

- It demonstrates the **core value of agents over plain LLMs**: an LLM alone cannot answer "what is the weather right now" correctly — it needs a tool
- It uses **exactly one tool** — simple enough to trace the full ReAct loop clearly
- The tool call involves **real HTTP data** — not a mock — making the output genuinely dynamic
- It demonstrates **anti-hallucination techniques**: system prompt grounding + Pydantic structured output to ensure the LLM cannot paraphrase or invent values
- It maps directly to the concepts in [01_What_Is_Agentic_AI.md](../Quick-Reference/01_What_Is_Agentic_AI.md) and [02_ReAct_Pattern_Deep_Dive.md](../Quick-Reference/02_ReAct_Pattern_Deep_Dive.md)

---

## 3. Step-by-Step Thought Process

### How a Human Would Solve This

```
1. User asks: "What is the weather in Paris?"
2. I recognise the intent: weather query for city = "Paris"
3. I open a weather website or app and search "Paris"
4. I read the result: "18°C, partly cloudy, wind 12 km/h"
5. I form a natural response: "It is currently 18°C and partly cloudy in Paris."
```

### How the Agent Solves This (ReAct Trace)

```
User: "What is the weather in Paris right now?"

Thought:   The user wants to know the current weather in Paris.
           I should call the get_weather tool with city = "Paris".

Action:    get_weather(city="Paris")

Observation: "Current weather in Paris, France: 18.2°C, Partly cloudy, wind speed 12.4 km/h."

Thought:   I now have the current weather data for Paris.
           I must populate the WeatherReport fields verbatim from the tool output.

Structured Output (WeatherReport):
  city                = "Paris, France"
  temperature_celsius = 18.2
  conditions          = "Partly cloudy"
  wind_speed_kmh      = 12.4
  summary             = "The current weather in Paris, France is 18.2°C with partly cloudy
                         skies and a wind speed of 12.4 km/h."

Final Answer: Paris, France: 18.2°C, Partly cloudy, wind 12.4 km/h.
              The current weather in Paris, France is 18.2°C with partly cloudy
              skies and a wind speed of 12.4 km/h.
```

### Decision Points in the Loop

```
┌────────────────────────────────────┐
│ User sends weather question        │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ Agent (LLM): parse city from input │
│ Decide: call get_weather tool      │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ Tool: HTTP GET Open-Meteo API      │
│ Geocode city → lat/lon             │
│ Fetch current weather data         │
└──────────────┬─────────────────────┘
               │
               ▼
┌────────────────────────────────────┐
│ Observation returned to agent      │
│ Agent: no more tool calls needed   │
│ Generate Final Answer              │
└──────────────┬─────────────────────┘
               │
               ▼
        Natural language response
```

---

## 4. Pseudo Code

```
FUNCTION weather_agent(user_question):

    # System prompt — prevents hallucination
    SYSTEM_PROMPT = "Always call the get_weather tool. Quote tool output verbatim."

    # Structured output schema — typed fields enforce grounding
    WeatherReport:
        city: str
        temperature_celsius: float
        conditions: str
        wind_speed_kmh: float
        summary: str

    # Tool definition
    TOOL get_weather(city: string) -> string:
        coords = geocode(city)               # city name → latitude, longitude
        weather = fetch_weather(coords)      # call Open-Meteo API
        RETURN formatted string with temp, conditions, wind

    # Agent setup
    llm = ChatOllama(model=OLLAMA_MODEL)
    agent = create_agent(
        model=llm,
        tools=[get_weather],
        system_prompt=SYSTEM_PROMPT,
        response_format=WeatherReport,
    )

    # Agent loop (handled internally by LangChain)
    LOOP:
        thought = llm.think(user_question, previous_observations)
        IF thought requires tool call:
            observation = get_weather(extracted_city)
            append observation to context
        ELSE:
            structured_response = WeatherReport(fields from tool output)
            RETURN formatted string from WeatherReport fields
        END IF
    END LOOP

END FUNCTION
```

---

## 5. High Level Workflow Diagram

This diagram shows the **user-facing flow** — what happens from the user's perspective at a conceptual level, without implementation detail.

```
┌─────────────────────────────────────────────────────────────────┐
│                   WEATHER REPORTING AGENT                       │
│                     High Level Flow                             │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────┐      Natural Language        ┌──────────────────┐
  │   User   │ ──────────────────────────► │  Weather Agent   │
  └──────────┘    "Weather in Tokyo?"       └────────┬─────────┘
                                                     │
                                          ┌──────────▼──────────┐
                                          │   Understands city  │
                                          │   = "Tokyo"         │
                                          └──────────┬──────────┘
                                                     │
                                          ┌──────────▼──────────┐
                                          │   Fetches live      │
                                          │   weather data      │
                                          └──────────┬──────────┘
                                                     │
  ┌──────────┐     Natural Language        ┌─────────▼──────────┐
  │   User   │ ◄────────────────────────── │  Formulates answer │
  └──────────┘  "22°C, partly cloudy..."   └────────────────────┘
```

**Key interactions at this level:**

| Actor | Role |
|---|---|
| **User** | Sends a natural language weather question for any city |
| **Weather Agent** | Interprets the question, fetches data, returns a natural language answer |
| **Weather API** | Provides real-time temperature, wind speed, and conditions |

---

## 6. Low Level Workflow Diagram

This diagram shows the **internal implementation flow** — every component, decision, and data transformation inside the agent.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        LOW LEVEL FLOW                               │
└─────────────────────────────────────────────────────────────────────┘

User Input
  │  "What is the weather in Tokyo right now?"
  │
  ▼
┌──────────────────────────────────────────┐
│  LangGraph: create_react_agent           │
│  MessagesState initialised               │
│  messages = [HumanMessage(content=...)]  │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  AGENT NODE                              │
│  ChatOllama.invoke(messages)             │
│  LLM reasoning:                          │
│    "I need to call get_weather(Tokyo)"   │
│  Output: AIMessage with tool_calls=      │
│    [{name: "get_weather",                │
│      args: {"city": "Tokyo"}}]           │
└──────────────────┬───────────────────────┘
                   │  tool call detected
                   ▼
┌──────────────────────────────────────────┐
│  CONDITIONAL EDGE: should_continue?      │
│  tool_calls present? → YES → tools node  │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  TOOLS NODE: get_weather(city="Tokyo")   │
│                                          │
│  Step 1 — Geocoding API call             │
│    GET geocoding-api.open-meteo.com      │
│    params: name="Tokyo", count=1         │
│    → lat=35.6895, lon=139.6917           │
│                                          │
│  Step 2 — Weather API call               │
│    GET api.open-meteo.com/v1/forecast    │
│    params: lat, lon, current=temp+wind   │
│    → temp=22.1°C, wind=8.5km/h, code=2  │
│                                          │
│  Step 3 — Map WMO code 2 → "Partly       │
│    cloudy"                               │
│                                          │
│  Returns: ToolMessage(content=           │
│    "Current weather in Tokyo, Japan:     │
│     22.1°C, Partly cloudy, wind 8.5")   │
└──────────────────┬───────────────────────┘
                   │
                   ▼
┌──────────────────────────────────────────┐
│  AGENT NODE (second pass)                │
│  ChatOllama.invoke(all messages)         │
│  WEATHER_SYSTEM_PROMPT enforces:         │
│    "Quote tool output verbatim"          │
│  response_format=WeatherReport enforces: │
│    typed fields — no free-form prose     │
│  Output: structured_response =           │
│    WeatherReport(                        │
│      city="Tokyo, Japan",                │
│      temperature_celsius=22.1,           │
│      conditions="Partly cloudy",         │
│      wind_speed_kmh=8.5,                 │
│      summary="The current weather..."    │
│    )                                     │
└──────────────────┬───────────────────────┘
                   │  no tool calls
                   ▼
┌──────────────────────────────────────────┐
│  CONDITIONAL EDGE: should_continue?      │
│  tool_calls absent? → NO → END           │
└──────────────────┬───────────────────────┘
                   │
                   ▼
            Final Answer returned
   "Tokyo, Japan: 22.1°C, Partly cloudy, wind 8.5 km/h.
    The current weather in Tokyo, Japan is 22.1°C with
    partly cloudy skies and a wind speed of 8.5 km/h."
```

**Data flow summary:**

```
HumanMessage
  └──► AIMessage (tool_calls)
         └──► ToolMessage (geocode + weather API results)
                └──► structured_response: WeatherReport (typed fields, no hallucination)
                       └──► Formatted string output
```

---

## 7. Implementation Steps

### Prerequisites

```
1. Virtual environment activated (projects/03_weather_reporting_agent/.venv)
2. common package installed: uv pip install -e ./common --python projects/03_weather_reporting_agent/.venv/Scripts/python.exe
3. Project dependencies installed: uv pip install -r requirements.txt (inside project venv)
4. .env file configured at repo root with OLLAMA_BASE_URL and OLLAMA_MODEL
5. Ollama server running with enough free RAM for your model
6. If using Multipass VM: ensure VM memory is sized to fit model + OS overhead
```

> **Note on `common` import**: The `uv` editable install does not always create the `.pth` file needed for `import common` to work. If you get `ModuleNotFoundError: No module named 'common'`, manually create:
> `projects/03_weather_reporting_agent/.venv/Lib/site-packages/ai_agent_common.pth`
> containing the absolute repo root path (e.g. `C:\Users\you\Agentic_AI_Development_Framework`).

### Step 1 — Install Additional Dependencies

The Open-Meteo API is accessed via HTTP. Add `requests` and `pydantic` to your project's requirements:

```bash
uv pip install requests pydantic
```

No API key or account is needed — Open-Meteo is a free, open-source weather API.

### Step 2 — Understand the Anti-Hallucination Strategy

Two complementary mechanisms prevent the LLM from inventing or paraphrasing weather data:

| Mechanism | How it works |
|---|---|
| `WEATHER_SYSTEM_PROMPT` | Instructs the LLM to quote tool output verbatim; forbids synonyms, rounding, and memory-based answers |
| `response_format=WeatherReport` | Pydantic schema with typed fields (`float` for temperature/wind) — the LLM must populate these, leaving no room for free-form fabrication |

### Step 3 — Understand the Two API Calls

The weather tool makes two sequential HTTP calls:

```
1. Geocoding API
   URL:  https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1
   Returns: latitude, longitude, timezone for the city name

2. Weather API
   URL:  https://api.open-meteo.com/v1/forecast
         ?latitude={lat}&longitude={lon}
         &current=temperature_2m,windspeed_10m,weathercode
         &timezone=auto
   Returns: current temperature, windspeed, and a WMO weather code
```

### Step 4 — Map WMO Weather Codes to Descriptions

The weather API returns a numeric **WMO weather code** (e.g., `0` = Clear sky, `61` = Rain).
The tool maps these to human-readable descriptions before returning to the agent.

### Step 5 — Run and Test

```powershell
cd projects/03_weather_reporting_agent

# Default demo — runs Tokyo, London, Sydney
python .\src\main.py

# Single city via CLI argument
python .\src\main.py Paris
python .\src\main.py "New York"

# Interactive mode — keep agent loaded, query any city
python .\src\main.py --interactive
# or: python .\src\main.py -i
```

Test with several cities to observe the full ReAct trace.

---

## 8. Code Snippets

### Full Implementation — `projects/03_weather_reporting_agent/src/main.py`

```python
"""
main.py — Weather Reporting Agent

ReAct agent that answers natural language weather questions for any city.
Uses the Open-Meteo API (free, no API key required).
"""

import argparse
import sys
import requests
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from common.llm_factory import get_chat_llm
from common.utils import get_logger

logger = get_logger(__name__)

# ── Anti-hallucination: system prompt enforces verbatim quoting ────────────────
WEATHER_SYSTEM_PROMPT = """You are a weather reporting assistant.

STRICT RULES:
- Always call the get_weather tool to answer weather questions. Never answer from memory or training data.
- Report the temperature, conditions, and wind speed EXACTLY as the tool returns them. Do not paraphrase, round, or substitute synonyms.
- If the tool says "Partly cloudy", output "Partly cloudy". Do NOT say "mostly cloudy" or "cloudy".
- If the tool says "12.4°C", output "12.4°C". Do NOT say "around 12°C" or any other value.
- Populate the structured response fields only with values taken directly from the tool output.
"""

# ── Anti-hallucination: structured output schema enforces typed fields ─────────
class WeatherReport(BaseModel):
    city: str = Field(description="City name exactly as returned by the tool")
    temperature_celsius: float = Field(description="Temperature exactly as returned by the tool")
    conditions: str = Field(description="Weather description exactly as returned by the tool")
    wind_speed_kmh: float = Field(description="Wind speed exactly as returned by the tool")
    summary: str = Field(description="One sentence using only the above fields, no invented data")

# ── WMO Weather Code → Human-readable description ─────────────────────────────
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Icy fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    80: "Slight showers", 81: "Moderate showers", 82: "Violent showers",
    95: "Thunderstorm", 96: "Thunderstorm with hail", 99: "Thunderstorm with heavy hail",
}


# ── Tool Definition ────────────────────────────────────────────────────────────
@tool
def get_weather(city: str) -> str:
    """
    Get the current weather for a given city name.
    Returns temperature in Celsius, wind speed in km/h, and weather description.
    """
    geo_response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1},
        timeout=10,
    )
    geo_response.raise_for_status()
    geo_data = geo_response.json()

    if not geo_data.get("results"):
        return f"City '{city}' not found. Please check the spelling."

    result = geo_data["results"][0]
    lat, lon = result["latitude"], result["longitude"]
    resolved_name = result["name"]
    country = result.get("country", "")

    weather_response = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,windspeed_10m,weathercode",
            "timezone": "auto",
        },
        timeout=10,
    )
    weather_response.raise_for_status()
    current = weather_response.json()["current"]

    temperature = current["temperature_2m"]
    windspeed = current["windspeed_10m"]
    description = WMO_CODES.get(current["weathercode"], f"Weather code {current['weathercode']}")

    logger.info("get_weather called for %s → %s°C, %s", city, temperature, description)
    return (
        f"Current weather in {resolved_name}, {country}: "
        f"{temperature}°C, {description}, wind speed {windspeed} km/h."
    )


# ── Agent Setup ────────────────────────────────────────────────────────────────
def build_agent():
    llm = get_chat_llm()
    return create_agent(
        model=llm,
        tools=[get_weather],
        system_prompt=WEATHER_SYSTEM_PROMPT,
        response_format=WeatherReport,
    )


# ── Run ────────────────────────────────────────────────────────────────────────
def ask(agent, question: str) -> str:
    result = agent.invoke({"messages": [HumanMessage(content=question)]})
    report: WeatherReport = result["structured_response"]
    return (
        f"{report.city}: {report.temperature_celsius}°C, "
        f"{report.conditions}, wind {report.wind_speed_kmh} km/h.\n"
        f"{report.summary}"
    )


def main():
    parser = argparse.ArgumentParser(description="Weather Reporting Agent")
    parser.add_argument("city", nargs="?", help="City name (e.g. 'Paris' or 'New York')")
    parser.add_argument("--interactive", "-i", action="store_true",
                        help="Start an interactive prompt loop")
    args = parser.parse_args()

    logger.info("Starting Weather Reporting Agent...")
    agent = build_agent()

    def _run(question: str) -> None:
        answer = ask(agent, question)
        print(f"\nQ: {question}\nA: {answer}\n" + "-" * 60)

    if args.city:
        _run(f"What is the current weather in {args.city}?")
    elif args.interactive:
        print("Weather Agent (interactive) — type a city or question, 'quit' to exit.\n")
        while True:
            try:
                user_input = input("Ask: ").strip()
            except (EOFError, KeyboardInterrupt):
                sys.exit(0)
            if not user_input:
                continue
            if user_input.lower() in {"quit", "exit", "q"}:
                sys.exit(0)
            _run(user_input)
    else:
        for q in [
            "What is the weather like in Tokyo right now?",
            "Tell me the current temperature in London.",
            "Is it raining in Sydney today?",
        ]:
            _run(q)


if __name__ == "__main__":
    main()
```

### Snippet — Tool Only (for unit testing)

```python
# Test the tool in isolation without running the full agent
from projects.weather_reporting_agent.src.main import get_weather

result = get_weather.invoke({"city": "Berlin"})
print(result)
# → "Current weather in Berlin, Germany: 12.4°C, Partly cloudy, wind speed 18.2 km/h."
```

### Snippet — Single City via CLI

```powershell
# From projects/03_weather_reporting_agent/
python .\src\main.py Paris
python .\src\main.py "New York"
```

### Snippet — Interactive Mode

```powershell
python .\src\main.py --interactive

Ask: Mumbai
Ask: Is it snowing in Hokkaido?
Ask: Compare weather in Oslo and Helsinki
Ask: quit
```

---

## 9. Test Cases

### How to Execute Tests

**Option A — Default demo (Tokyo, London, Sydney):**
```powershell
cd projects/03_weather_reporting_agent
python .\src\main.py
```

**Option B — Single city via CLI:**
```powershell
python .\src\main.py Berlin
```

**Option C — Interactive mode:**
```powershell
python .\src\main.py -i
```

**Option D — Test the tool in isolation (no LLM needed):**
```powershell
python .\src\tool_test.py
```
```python
# tool_test.py — run from projects/03_weather_reporting_agent/
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
from src.main import get_weather
print(get_weather.invoke({'city': 'Paris'}))
```

---

### Test Case Scenarios

#### TC-01 — Valid City (Major World City)

| Field | Value |
|---|---|
| **Input** | `"What is the weather like in Tokyo right now?"` |
| **Expected Tool Call** | `get_weather(city="Tokyo")` |
| **Expected Observation** | String containing temperature in °C, wind speed, and weather description |
| **Expected Final Answer** | Natural language sentence with Tokyo's current temperature and conditions |
| **Pass Criteria** | Response contains a numeric temperature value and mentions Tokyo |

```python
result = ask(agent, "What is the weather like in Tokyo right now?")
assert "Tokyo" in result
assert "°C" in result or "celsius" in result.lower() or any(char.isdigit() for char in result)
```

---

#### TC-02 — Valid City (Different Continent)

| Field | Value |
|---|---|
| **Input** | `"Tell me the current temperature in London."` |
| **Expected Tool Call** | `get_weather(city="London")` |
| **Expected Observation** | String with London's temperature, wind, and conditions |
| **Expected Final Answer** | Natural language answer mentioning London and a temperature value |
| **Pass Criteria** | Response contains a numeric value and mentions London |

---

#### TC-03 — Weather Condition Query (Rain Check)

| Field | Value |
|---|---|
| **Input** | `"Is it raining in Sydney today?"` |
| **Expected Tool Call** | `get_weather(city="Sydney")` |
| **Expected Observation** | String with Sydney's conditions (rain-related code or not) |
| **Expected Final Answer** | A yes/no answer about rain with supporting conditions |
| **Pass Criteria** | Response mentions Sydney and addresses the rain question directly |

---

#### TC-04 — Multi-City Comparison

| Field | Value |
|---|---|
| **Input** | `"Compare the weather in Paris and Berlin."` |
| **Expected Tool Calls** | `get_weather(city="Paris")` AND `get_weather(city="Berlin")` (two calls) |
| **Expected Final Answer** | Comparison of both cities' conditions in one response |
| **Pass Criteria** | Response mentions both Paris and Berlin with distinct weather values |

```python
result = ask(agent, "Compare the weather in Paris and Berlin.")
assert "Paris" in result
assert "Berlin" in result
```

---

#### TC-05 — Invalid / Misspelled City

| Field | Value |
|---|---|
| **Input** | `"What is the weather in Xyzabc123?"` |
| **Expected Tool Call** | `get_weather(city="Xyzabc123")` |
| **Expected Observation** | `"City 'Xyzabc123' not found. Please check the spelling."` |
| **Expected Final Answer** | Agent politely informs the user the city was not found |
| **Pass Criteria** | Response does NOT contain a temperature value; mentions city not found |

```python
result = ask(agent, "What is the weather in Xyzabc123?")
assert "not found" in result.lower() or "couldn't find" in result.lower() or "unable" in result.lower()
```

---

#### TC-06 — Tool Isolation Test (No LLM)

Test the `get_weather` tool directly without the agent to verify the API integration works independently.

| Field | Value |
|---|---|
| **Input** | `get_weather.invoke({"city": "Berlin"})` |
| **Expected Output** | String starting with `"Current weather in Berlin, Germany:"` |
| **Pass Criteria** | Output contains `°C`, `km/h`, and a weather description word |

```python
from projects.weather_reporting_agent.src.main import get_weather

result = get_weather.invoke({"city": "Berlin"})
assert "Berlin" in result
assert "°C" in result
assert "km/h" in result
print("TC-06 PASSED:", result)
```

---

#### TC-07 — Non-English City Name

| Field | Value |
|---|---|
| **Input** | `"What is the weather in München?"` |
| **Expected Tool Call** | `get_weather(city="München")` |
| **Expected Observation** | Weather data for Munich, Germany |
| **Expected Final Answer** | Natural language answer referencing Munich/München |
| **Pass Criteria** | Tool resolves the non-ASCII city name and returns valid weather |

---

#### TC-08 — CLI City Argument

| Field | Value |
|---|---|
| **Input** | `python .\src\main.py Paris` |
| **Expected** | Single weather report for Paris printed to stdout |
| **Pass Criteria** | Output contains "Paris", a temperature float, and a conditions string |

---

#### TC-09 — Structured Output Integrity (Anti-Hallucination)

| Field | Value |
|---|---|
| **Purpose** | Verify `WeatherReport` fields match what the tool returned, not invented values |
| **Method** | Capture tool output string; parse temperature from it; compare to `report.temperature_celsius` |
| **Pass Criteria** | `abs(parsed_temp - report.temperature_celsius) < 0.1` — no rounding or substitution |

---

### Test Results Table

After running the tests, record results here:

| TC | Description | Status | Notes |
|---|---|---|---|
| TC-01 | Valid city — Tokyo | ⬜ Not run | |
| TC-02 | Valid city — London | ⬜ Not run | |
| TC-03 | Rain condition — Sydney | ⬜ Not run | |
| TC-04 | Multi-city comparison | ⬜ Not run | |
| TC-05 | Invalid city name | ⬜ Not run | |
| TC-06 | Tool isolation test | ⬜ Not run | |
| TC-07 | Non-English city name | ⬜ Not run | |
| TC-08 | CLI city argument | ⬜ Not run | |
| TC-09 | Structured output integrity | ⬜ Not run | |

> Update the Status column to ✅ Pass, ❌ Fail, or ⚠️ Partial as you run each case.

---

## 10. Expected Outcomes

### What You Should See

Running `python .\src\main.py` (default demo) will print three Q&A pairs in structured format:

```
Q: What is the weather like in Tokyo right now?
A: Tokyo, Japan: 12.4°C, Partly cloudy, wind 2.6 km/h.
   The current weather in Tokyo, Japan is 12.4°C with partly cloudy skies and a wind speed of 2.6 km/h.
------------------------------------------------------------

Q: Tell me the current temperature in London.
A: London, United Kingdom: 14.3°C, Overcast, wind 21.0 km/h.
   The current weather in London, United Kingdom is 14.3°C with overcast skies and a wind speed of 21.0 km/h.
------------------------------------------------------------

Q: Is it raining in Sydney today?
A: Sydney, Australia: 26.8°C, Mainly clear, wind 15.2 km/h.
   It is not currently raining in Sydney, Australia. The temperature is 26.8°C with mainly clear skies.
------------------------------------------------------------
```

> Exact values will vary — they are live weather readings from Open-Meteo at time of execution.
> The format is deterministic because it is assembled from typed `WeatherReport` fields, not LLM prose.

### ReAct Trace (What Happens Internally)

For the question _"What is the weather like in Tokyo right now?"_:

```
[HumanMessage]       "What is the weather like in Tokyo right now?"

[AIMessage]          tool_calls=[{name: "get_weather", args: {"city": "Tokyo"}}]

[ToolMessage]        "Current weather in Tokyo, Japan: 12.4°C, Partly cloudy,
                      wind speed 2.6 km/h."

[structured_response] WeatherReport(
                        city="Tokyo, Japan",
                        temperature_celsius=12.4,
                        conditions="Partly cloudy",
                        wind_speed_kmh=2.6,
                        summary="The current weather in Tokyo, Japan is 12.4°C..."
                      )
```

### Verification Checklist

| Check | Expected Result |
|---|---|
| Agent calls `get_weather` tool | ✅ `ToolMessage` appears in message history |
| Tool returns real weather data | ✅ Values change between runs and match actual Open-Meteo readings |
| Output fields match tool data | ✅ `WeatherReport.temperature_celsius` equals the value in `ToolMessage` — no rounding or substitution |
| LLM cannot hallucinate values | ✅ `float` fields in `WeatherReport` prevent invented temperatures or wind speeds |
| CLI city argument works | ✅ `python .\src\main.py Paris` returns Paris weather only |
| Interactive mode works | ✅ `python .\src\main.py -i` keeps agent resident; each prompt queries a new city |
| Unknown city handled gracefully | ✅ Tool returns "City not found" message; agent relays this to user |
| Network error handled | ✅ `requests` raises `HTTPError`; agent surfaces the error in its response |

### What to Experiment With Next

| Experiment | How |
|---|---|
| Add a second tool | Create `get_forecast(city, days)` for multi-day forecasts |
| Add memory | Pass a `MemorySaver` checkpointer so the agent remembers conversation history across `ask()` calls |
| Multi-city query | Ask "Compare the weather in Paris and Berlin" in interactive mode — watch the agent call the tool twice |
| Streaming output | Use `agent.stream(...)` instead of `agent.invoke(...)` to print tokens as they arrive |
| Switch weather provider | Replace Open-Meteo with OpenWeatherMap or Tomorrow.io for station-based (more accurate) readings |
| Add humidity & UV | Extend the `WeatherReport` schema and request `relativehumidity_2m,uv_index` from the API |

---

*Back to planner index → [`planner/`](../planner/)*  
*Related Quick-Reference → [02_ReAct_Pattern_Deep_Dive.md](../Quick-Reference/02_ReAct_Pattern_Deep_Dive.md)*
